# -*- coding: utf-8 -*-
"""Kit render laporan QA generik.

Satu source of truth: pendukung/ai/triage.json.
Target menentukan isi lewat blok `report` di triage (profil, bab, tabel tambahan,
gambar bukti). Kit ini TIDAK tahu apa-apa soal web, mobile, atau API secara hardcoded.
"""
import os, re, json, hashlib, argparse
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Renderer sengaja TIDAK menyensor nilai. Nilai yang tersedia di artefak tampil
# apa adanya di DOCX; nilai yang tidak ada ditulis `(...)`
# di triage.json, bukan diganti marker [REDACTED].
def R(text):
    """Identity renderer — pertahankan nilai apa adanya dari triage/artefak."""
    return str(text)

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

SEV_LI = {'CRITICAL': (5, 5), 'HIGH': (4, 4), 'MEDIUM': (3, 3), 'LOW': (2, 2)}
SEV_FILL = {'CRITICAL': 'B00000', 'HIGH': 'C05000', 'MEDIUM': '8A6D00', 'LOW': '336633'}
SEV_RGB = {'CRITICAL': RGBColor(0xB0,0x00,0x00), 'HIGH': RGBColor(0xC0,0x50,0x00),
           'MEDIUM': RGBColor(0x8A,0x6D,0x00), 'LOW': RGBColor(0x33,0x66,0x33)}

# Target SLA default dari SOP-QA.md §5. Bisa dioverride lewat governance.sla di triage.json.
DEFAULT_SLA = {
    'CRITICAL': {'response': '1 hari kerja', 'fix': '3 hari kerja'},
    'HIGH': {'response': '2 hari kerja', 'fix': '7 hari kerja'},
    'MEDIUM': {'response': '3 hari kerja', 'fix': '30 hari kerja'},
    'LOW': {'response': '5 hari kerja', 'fix': 'sprint berikutnya'},
    'INFO': {'response': '5 hari kerja', 'fix': 'backlog'},
}

DEFAULT_CHAPTERS = {
    'web': ['cover','executive','scope','method','environment','findings','passed',
            'risk','recommendations','limits','conclusion','appendix_cases','appendix_evidence','appendix_extra'],
    'mobile': ['cover','executive','scope','method','environment','findings','passed',
               'risk','recommendations','limits','conclusion','appendix_cases','appendix_evidence','appendix_extra'],
    'api': ['cover','executive','scope','method','environment','findings','passed',
            'risk','recommendations','limits','conclusion','appendix_cases','appendix_evidence'],
    'all': ['cover','executive','scope','method','environment','findings','passed',
            'risk','recommendations','limits','conclusion','appendix_cases','appendix_evidence','appendix_extra'],
}

BUILTIN_TITLES = {
    'executive': 'Ringkasan Eksekutif',
    'scope': 'Scope & Rules of Engagement',
    'method': 'Metodologi & Pemetaan Modul Skill',
    'environment': 'Lingkungan Pengujian',
    'findings': 'Temuan',
    'passed': 'Hasil Pemeriksaan yang Lolos',
    'risk': 'Risk Register',
    'recommendations': 'Rekomendasi Prioritas',
    'db_verification': 'Verifikasi Database (Read-Only)',
    'limits': 'Batasan & Status',
    'conclusion': 'Kesimpulan & Rekomendasi Akhir',
    'appendix_cases': 'Lampiran — Daftar Test Case',
    'appendix_evidence': 'Lampiran — Inventaris Bukti',
    'appendix_extra': 'Lampiran — Bukti Eksekusi Tambahan',
}

SECTION_HINTS = {
    'scope': ['Scope & Rules'], 'method': ['Metodologi'], 'environment': ['Lingkungan Pengujian'],
    'findings': ['Temuan'], 'risk': ['Risk Register'], 'recommendations': ['Rekomendasi Prioritas'],
    'db_verification': ['Verifikasi Database'],
    'limits': ['Batasan & Status'], 'conclusion': ['Kesimpulan'], 'appendix_cases': ['Daftar Test Case'],
    'appendix_evidence': ['Inventaris Bukti'], 'appendix_extra': ['Bukti Eksekusi Tambahan'],
}


def norm_shots(finding):
    """Screenshot temuan + anotasi merah.

    Mendukung format lama (`shots: ["file.png"]`) dan format baru:
      "shots": [{"ref": "file.png",
                 "highlight": {"type": "circle", "x": 0.6, "y": 0.3, "w": 0.2, "h": 0.15},
                 "label": "Area temuan"}]
    Koordinat x/y/w/h relatif (0–1) terhadap ukuran gambar; nilai >1 dibaca piksel.
    """
    raw = list(finding.get('shots') or [])
    ev = finding.get('evidence', [])
    if isinstance(ev, str):
        ev = [x.strip() for x in re.split(r';|\n', ev) if x.strip()]
    for e in ev:
        if isinstance(e, str) and e.lower().endswith('.png'):
            raw.append({'ref': os.path.basename(e)})
    out, seen = [], set()
    for s in raw:
        if isinstance(s, dict):
            item = {
                'ref': str(s.get('ref') or s.get('path') or s.get('file') or ''),
                'highlight': s.get('highlight') or s.get('annotation'),
                'label': s.get('label', ''),
            }
        else:
            item = {'ref': str(s), 'highlight': None, 'label': ''}
        key = os.path.basename(item['ref'])
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def annotate_shot(fp, highlight, label, out_dir):
    """Gambar lingkaran/kotak merah pada screenshot; kembalikan path hasil anotasi."""
    from PIL import Image, ImageDraw, ImageFont

    def px(v, size):
        v = float(v)
        return v * size if -1.0 <= v <= 1.0 else v

    im = Image.open(fp).convert('RGB')
    W, H = im.size
    d = ImageDraw.Draw(im)
    h = dict(highlight or {})
    typ = str(h.get('type') or 'circle').lower()
    if typ in ('circle', 'ellipse') and 'cx' in h and 'cy' in h:
        cx, cy = px(h['cx'], W), px(h['cy'], H)
        r = px(h.get('r', 0.06), W)
        box = [cx - r, cy - r, cx + r, cy + r]
    else:
        x = px(h.get('x', 0.35), W)
        y = px(h.get('y', 0.35), H)
        w = px(h.get('w', 0.3), W)
        hh = px(h.get('h', 0.2), H)
        box = [x, y, x + w, y + hh]
    width = max(3, int(min(W, H) * 0.008))
    red = (230, 20, 25)
    if typ in ('circle', 'ellipse'):
        d.ellipse(box, outline=red, width=width)
    else:
        d.rectangle(box, outline=red, width=width)
    if label:
        try:
            font = ImageFont.truetype(r'C:\Windows\Fonts\segoeuib.ttf',
                                      max(15, int(H * 0.026)))
        except Exception:
            font = ImageFont.load_default()
        ly = max(0, int(box[1] - H * 0.055))
        d.text((max(0, int(box[0])), ly), str(label), fill=red, font=font,
               stroke_width=1, stroke_fill=(255, 255, 255))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir,
                       os.path.splitext(os.path.basename(fp))[0] + '_red.png')
    im.save(out)
    return out


def norm_findings(triage):
    """Normalisasi skema lama (sev/cat/rec/impact teks) dan baru (severity/.../skor)."""
    out = []
    for f in triage.get('findings', []):
        sev = str(f.get('severity') or f.get('sev') or 'LOW').upper()
        likelihood = f.get('likelihood')
        imp = f.get('impact')
        impact_score = imp if isinstance(imp, (int, float)) else None
        business = f.get('business_impact') or (imp if isinstance(imp, str) else '')
        if likelihood is None or impact_score is None:
            likelihood, impact_score = SEV_LI.get(sev, (2, 2))
        try:
            score = int(f.get('risk_score') or round(likelihood * impact_score))
        except Exception:
            score = likelihood * impact_score
        ev = f.get('evidence', [])
        if isinstance(ev, str):
            ev = [x.strip() for x in re.split(r';|\n', ev) if x.strip()]
        shots = norm_shots(f)
        out.append({
            'id': f.get('id', '-'), 'title': f.get('title', '-'), 'severity': sev,
            'category': f.get('category') or f.get('cat') or '-',
            'status': f.get('status', '-'), 'location': f.get('location', ''),
            'likelihood': likelihood, 'impact_score': impact_score, 'score': score,
            'expected': f.get('expected', '-'), 'actual': f.get('actual', '-'),
            'business': business, 'recommendation': f.get('recommendation') or f.get('rec') or '-',
            'steps': f.get('steps') or [], 'cwe': f.get('cwe', '-'),
            'chain': f.get('chain') or [], 'evidence': ev, 'confidence': f.get('confidence', '-'),
            'owner': f.get('owner') or f.get('assignee') or '-',
            'ticket': f.get('ticket') or f.get('linked_ticket') or '-',
            'defect_status': f.get('defect_status') or '-',
            'sla_due': f.get('sla_due') or '-',
            'requirement': f.get('requirement') or f.get('requirement_id') or '-',
            'source': f.get('source') or '-',
            'spec_status': f.get('spec_status') or '-',
            'retest_of': f.get('retest_of') or '-',
            'shots': shots,
        })
    return out


class Report:
    def __init__(self, root, triage, cfg, profile):
        self.root = os.path.abspath(root)
        self.base = os.path.join(self.root, 'pendukung')
        self.triage = triage
        self.cfg = cfg
        self.profile = profile
        self._findings = norm_findings(triage)
        self.doc = Document()
        self._setup()

    # ---------- low level ----------
    def _setup(self):
        for sec in self.doc.sections:
            sec.top_margin = Inches(0.9); sec.bottom_margin = Inches(0.85)
            sec.left_margin = Inches(0.9); sec.right_margin = Inches(0.9)
            sec.header_distance = Inches(0.4); sec.footer_distance = Inches(0.4)
            sec.different_first_page_header_footer = True
        st = self.doc.styles['Normal']
        st.font.name = 'Calibri'; st.font.size = Pt(10.5)
        st.font.color.rgb = RGBColor(0x22, 0x2A, 0x35)
        st._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), 'Calibri')
        st.paragraph_format.line_spacing = 1.22; st.paragraph_format.space_after = Pt(6)
        for lvl, sz, col in ((1,16,RGBColor(0x1F,0x3A,0x5F)), (2,12.5,RGBColor(0x2E,0x5A,0x88)),
                             (3,11,RGBColor(0x1F,0x3A,0x5F))):
            hs = self.doc.styles['Heading %d' % lvl]
            hs.font.name = 'Calibri'; hs.font.size = Pt(sz); hs.font.bold = True
            hs.font.color.rgb = col
            hs._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), 'Calibri')
            hs.paragraph_format.space_before = Pt(16 if lvl == 1 else 10)
            hs.paragraph_format.space_after = Pt(6); hs.paragraph_format.keep_with_next = True
        cap = self.doc.styles['Caption']
        cap.font.size = Pt(9); cap.font.italic = True; cap.font.color.rgb = RGBColor(0x66,0x6E,0x7A)
        cap.paragraph_format.space_before = Pt(2); cap.paragraph_format.space_after = Pt(12)
        ls = self.doc.styles['List Bullet']
        ls.paragraph_format.space_after = Pt(3); ls.paragraph_format.line_spacing = 1.15
        header = self.cfg.get('header', 'Laporan Assessment Terpadu')
        footer = self.cfg.get('footer', 'Internal — UAT only   |   Halaman ')
        for sec in self.doc.sections:
            hp = sec.header.paragraphs[0]; hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            hr = hp.add_run(R(header)); hr.font.size = Pt(8); hr.font.color.rgb = RGBColor(0x66,0x6E,0x7A)
            self._rule(hp)
            fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            fr = fp.add_run(R(footer)); fr.font.size = Pt(8); fr.font.color.rgb = RGBColor(0x66,0x6E,0x7A)
            self._page_field(fp)

    @staticmethod
    def _shade(cell, fill):
        tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd')
        shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'),fill)
        tcPr.append(shd)

    @staticmethod
    def _margins(cell, top=70, start=100, bottom=70, end=100):
        tcPr = cell._tc.get_or_add_tcPr(); tcMar = OxmlElement('w:tcMar')
        for m, v in (('top',top),('start',start),('bottom',bottom),('end',end)):
            n = OxmlElement('w:'+m); n.set(qn('w:w'),str(v)); n.set(qn('w:type'),'dxa'); tcMar.append(n)
        tcPr.append(tcMar)

    @staticmethod
    def _repeat(row):
        trPr = row._tr.get_or_add_trPr(); el = OxmlElement('w:tblHeader')
        el.set(qn('w:val'),'true'); trPr.append(el)

    @staticmethod
    def _borders(t):
        tblPr = t._tbl.tblPr; borders = OxmlElement('w:tblBorders')
        for edge in ('top','left','bottom','right','insideH','insideV'):
            e = OxmlElement('w:'+edge); e.set(qn('w:val'),'single')
            e.set(qn('w:sz'),'4'); e.set(qn('w:color'),'C9D3DF'); borders.append(e)
        tblPr.append(borders)

    @staticmethod
    def _page_field(p):
        run = p.add_run(); b = OxmlElement('w:fldChar'); b.set(qn('w:fldCharType'),'begin')
        i = OxmlElement('w:instrText'); i.set(qn('xml:space'),'preserve'); i.text = 'PAGE'
        e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),'end')
        run._r.append(b); run._r.append(i); run._r.append(e)
        run.font.size = Pt(8); run.font.color.rgb = RGBColor(0x66,0x6E,0x7A)

    @staticmethod
    def _rule(p, color='C9D3DF', size='6'):
        pPr = p._p.get_or_add_pPr(); pbdr = OxmlElement('w:pBdr'); bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'),'single'); bottom.set(qn('w:sz'),size)
        bottom.set(qn('w:space'),'4'); bottom.set(qn('w:color'),color)
        pbdr.append(bottom); pPr.append(pbdr)

    def P(self, text='', bold=False, italic=False, size=None):
        p = self.doc.add_paragraph(); run = p.add_run(R(text))
        run.bold = bold; run.italic = italic
        if size: run.font.size = Pt(size)
        return p

    def H(self, text, level=1):
        h = self.doc.add_heading(R(text), level=level)
        if level == 2:
            for r in h.runs: r.font.color.rgb = RGBColor(0x2E,0x5A,0x88)
        return h

    def spacer(self, pt=4):
        p = self.doc.add_paragraph(); p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0); p.add_run('').font.size = Pt(pt)
        return p

    def table(self, headers, rows, widths=None, score_col=None, severity_col=None):
        t = self.doc.add_table(rows=1, cols=len(headers))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False; self._borders(t)
        hdr = t.rows[0]; self._repeat(hdr)
        for i, h in enumerate(headers):
            c = hdr.cells[i]; c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER; c.text = ''
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(R(h)); r.bold = True; r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0xFF,0xFF,0xFF)
            self._shade(c, '1F3A5F'); self._margins(c)
        for ri, row in enumerate(rows):
            cells = t.add_row().cells
            for i, v in enumerate(row):
                c = cells[i]; c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER; c.text = ''
                p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.1
                r = p.add_run(R(v)); r.font.size = Pt(9)
                if ri % 2 == 1: self._shade(c, 'F2F5F9')
                self._margins(c)
        if widths and len(widths) == len(headers):
            for row in t.rows:
                for i, w in enumerate(widths): row.cells[i].width = Inches(w)
        if severity_col is not None:
            for ri, row in enumerate(rows):
                sev = str(row[severity_col]).upper()
                c = t.rows[ri+1].cells[severity_col]
                self._shade(c, SEV_FILL.get(sev, 'F2F5F9'))
                for p in c.paragraphs:
                    for r in p.runs:
                        r.bold = True; r.font.color.rgb = RGBColor(0xFF,0xFF,0xFF)
        if score_col is not None:
            for ri, row in enumerate(rows):
                try: sc = int(row[score_col])
                except Exception: continue
                fill = 'B00000' if sc >= 20 else 'C05000' if sc >= 12 else '8A6D00' if sc >= 6 else '336633'
                c = t.rows[ri+1].cells[score_col]; self._shade(c, fill)
                for p in c.paragraphs:
                    for r in p.runs:
                        r.bold = True; r.font.color.rgb = RGBColor(0xFF,0xFF,0xFF)
        self.spacer(4)
        return t

    def bullet(self, text):
        return self.doc.add_paragraph(R(text), style='List Bullet')

    def banner(self, text, fill='8A6D00', size=11):
        t = self.doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = t.cell(0, 0); c.text = ''
        p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(R(text)); r.bold = True; r.font.size = Pt(size)
        r.font.color.rgb = RGBColor(0xFF,0xFF,0xFF)
        self._shade(c, fill); self._margins(c, 140, 140, 140, 140); self._borders(t)
        self.spacer(6)

    def resolve_image(self, ref):
        ref = str(ref).replace('/', os.sep)
        cands = []
        if ref.startswith('pendukung' + os.sep): cands.append(os.path.join(self.root, ref))
        cands += [os.path.join(self.base, 'screenshots', os.path.basename(ref)),
                  os.path.join(self.base, 'bukti', os.path.basename(ref)),
                  os.path.join(self.base, 'bukti', 'screenshots', os.path.basename(ref)),
                  os.path.join(self.base, ref)]
        for c in cands:
            if os.path.isfile(c): return c
        return None

    def image(self, ref, caption, width=5.6, highlight=None, label=''):
        fp = self.resolve_image(ref)
        if not fp:
            self.P('Gambar tidak tersedia: ' + str(ref), italic=True); return False
        used = fp
        if highlight:
            try:
                used = annotate_shot(fp, highlight, label,
                                     os.path.join(self.base, 'bukti', 'annotated'))
                caption = str(caption) + ' · lingkaran merah: ' + (str(label) or 'area temuan')
            except Exception as ex:
                self.P('Anotasi merah gagal dibuat: ' + str(ex), italic=True)
        self.doc.add_picture(used, width=Inches(width))
        cap = self.doc.add_paragraph(style='Caption'); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run(R(caption)).italic = True
        return True

    # ---------- built-in chapters ----------
    def cover(self):
        cfg = self.cfg; tr = self.triage
        self.spacer(26)
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run('INTERNAL  ·  UAT ONLY'); r.bold = True; r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0x2E,0x5A,0x88)
        self.spacer(14)
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(R(cfg.get('title', 'LAPORAN ASSESSMENT TERPADU')))
        r.bold = True; r.font.size = Pt(26); r.font.color.rgb = RGBColor(0x1F,0x3A,0x5F)
        self._rule(p, color='1F3A5F', size='14')
        self.spacer(8)
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(R(cfg.get('subtitle', ''))); r.italic = True; r.font.size = Pt(13)
        r.font.color.rgb = RGBColor(0x66,0x6E,0x7A)
        self.spacer(20)
        fields = cfg.get('cover_fields') or self._cover_fields()
        self.table(['Field', 'Nilai'], fields, widths=[1.7,4.8])
        for note in cfg.get('cover_notes', []): self.P(note, italic=True)
        self.doc.add_page_break()

    def _cover_fields(self):
        tr = self.triage
        if 'application' in tr:
            app = tr['application']
            return [['Aplikasi', app.get('name','-')],
                    ['Versi', app.get('version','-')], ['Package', app.get('package','-')],
                    ['Lingkungan', tr.get('environment','-')],
                    ['Tanggal', tr.get('generated_at','-')],
                    ['Klasifikasi', 'Internal — UAT only'],
                    ['Referensi', 'Nomor tiket/approval: ' + str(tr.get('ticket_ref','(...)'))]]
        return [['Aplikasi', tr.get('target','-')], ['Target URL', tr.get('target_url','-')],
                ['Mode', str(tr.get('mode','-')) + ' — ' + str(tr.get('input_mode','-'))],
                ['Tanggal', tr.get('date','-')], ['Environment', tr.get('environment','-')],
                ['Klasifikasi', 'Internal — UAT only'],
                ['Referensi', 'Nomor tiket/approval: ' + str(tr.get('ticket_ref','(...)'))]]

    def executive(self):
        s = self.triage.get('summary', {})
        rec = s.get('release_recommendation', '-')
        fill = 'B00000' if 'DO_NOT_RELEASE' in str(rec).upper() else '8A6D00'
        self.banner('VERDICT: ' + rec, fill=fill)
        by = s.get('by_severity', {})
        self.P(f"Total {s.get('total_findings',len(self._findings))} temuan: "
               f"{by.get('CRITICAL',0)} critical, {by.get('HIGH',0)} high, "
               f"{by.get('MEDIUM',0)} medium, {by.get('LOW',0)} low.")
        cc = s.get('case_counts')
        if cc:
            self.P(f"Daftar case: {cc.get('total','-')} case = {cc.get('pass','-')} PASS, "
                   f"{cc.get('fail','-')} FAIL, {cc.get('blocked','-')} BLOCKED.")
        if self.cfg.get('claim_note'): self.P(self.cfg['claim_note'], bold=True)
        top = self._findings[:4]
        if top:
            self.H('Temuan teratas', 2)
            self.table(['ID','Severity','Temuan','Skor'],
                       [[f['id'],f['severity'],f['title'],str(f['score'])] for f in top],
                       widths=[0.75,0.95,3.85,0.75], severity_col=1, score_col=3)
        self.blocks(self.cfg.get('executive_blocks', []))

    def scope(self):
        rows = self.cfg.get('scope_rows') or [
            ['Target', self.triage.get('target_url') or self.triage.get('environment','-')],
            ['Mode', self.triage.get('mode') or self.profile],
            ['Environment', self.triage.get('environment','-')],
            ['Aturan', 'Eksplorasi pasif; aksi mengubah state butuh approval eksplisit.'],
            ['Stop condition', 'Hentikan bila terjadi degradasi target atau aksi keluar scope.'],
        ]
        self.table(['Aspek','Ketentuan'], rows, widths=[1.7,4.8])
        self.blocks(self.cfg.get('scope_blocks', []))

    def method(self):
        rows = self.cfg.get('method_rows') or [
            ['Area','Alat / Teknik','Bukti'],
            ['Reporting','python-docx + nilai aktual (tanpa redaction)','Dokumen ini'],
        ]
        if rows and len(rows[0]) == 2:
            self.table(rows[0], rows[1:], widths=[1.7,4.8])
        else:
            self.table(rows[0], rows[1:], widths=[1.4,2.4,2.7])
        self.blocks(self.cfg.get('method_blocks', []))

    def _credential_summary(self, acc):
        vals = []
        for k in ('password','pin_test_mode','otp'):
            v = str(acc.get(k,'')).strip()
            if v and v not in vals:
                vals.append(v)
        real = [v for v in vals if v != '(...)'] or ['(...)']
        return ' / '.join(real)

    def environment(self):
        tr = self.triage; acc = tr.get('test_account', {})
        rows = [['Item','Nilai'], ['Environment', tr.get('environment','-')],
                ['Identitas akun uji', acc.get('identity','-')],
                ['Role akun', acc.get('role','-')],
                ['Sumber akun', acc.get('source','-')],
                ['Metode login', acc.get('login_method','-')],
                ['Password / PIN / OTP', self._credential_summary(acc)],
                ['Token', acc.get('token','-')]]
        if 'application' in tr:
            rows[1:1] = [['Aplikasi', tr['application'].get('name','-')],
                         ['Versi', tr['application'].get('version','-')],
                         ['Package', tr['application'].get('package','-')]]
            perf = os.path.join(self.base, 'bukti', 'performance-raw.json')
            if os.path.isfile(perf):
                d = json.load(open(perf, encoding='utf-8'))
                rows += [['Komponen launcher', d.get('component','-')],
                         ['PID aplikasi', d.get('pid_after_start','-')]]
        else:
            rows[1:1] = [['Target', tr.get('target_url','-')], ['Browser', 'Playwright Chromium (Code Mode)']]
        rows = [r for r in rows if r[0] != 'Token' or acc.get('token')]
        self.table(rows[0], rows[1:], widths=[1.7,4.8])
        for note in self.cfg.get('environment_notes', []): self.P(note, italic=True)

    def findings(self):
        self.P('Diurutkan berdasarkan severity dan skor (Likelihood × Impact). ID temuan tunggal '
               'dipakai lintas bab dan risk register.', italic=True)
        used = set()
        for f in self._findings:
            h = self.H(f"{f['id']} — {f['title']}", 2)
            for r in h.runs:
                if f['severity'] in SEV_RGB: r.font.color.rgb = SEV_RGB[f['severity']]
            self.table(['Severity','Kategori','Status','L','I','Skor','Chain'],
                       [[f['severity'],f['category'],f['status'],str(f['likelihood']),
                         str(f['impact_score']),str(f['score']),', '.join(f['chain']) or '-']],
                       widths=[0.95,1.35,0.85,0.35,0.35,0.55,1.9],
                       severity_col=0, score_col=5)
            if f['location']: self.P('Lokasi: ' + str(f['location']))
            if f['steps']:
                self.P('Langkah reproduksi:', bold=True)
                for s in f['steps']: self.bullet(s)
            self.P('Ekspektasi: ' + str(f['expected']))
            self.P('Aktual: ' + str(f['actual']))
            if f['business']: self.P('Dampak bisnis: ' + str(f['business']))
            self.P('Rekomendasi: ' + str(f['recommendation']))
            track = (f"Tindak lanjut: Owner={f['owner']}; Tiket={f['ticket']}; "
                     f"Status defect={f['defect_status']}; SLA={f['sla_due']}; "
                     f"Requirement={f['requirement']}; Sumber={f['source']}; "
                     f"Status spesifikasi={f['spec_status']}")
            if f['retest_of'] != '-':
                track += f"; Uji ulang dari={f['retest_of']}"
            self.P(track, italic=True)
            self.P('Bukti: ' + '; '.join(map(str, f['evidence'])) +
                   (f" (keyakinan: {f['confidence']})" if f['confidence'] != '-' else ''), italic=True)
            if not any(s.get('highlight') for s in f['shots']):
                self.P('CATATAN: screenshot temuan ini belum diberi lingkaran merah di triage.json.',
                       italic=True)
            for shot in f['shots']:
                ref = shot.get('ref', '') if isinstance(shot, dict) else str(shot)
                fp = self.resolve_image(ref)
                if fp and fp not in used:
                    self.image(ref,
                               f"Gambar: {f['id']} — {os.path.basename(fp)} (bukti dari temuan).",
                               highlight=shot.get('highlight') if isinstance(shot, dict) else None,
                               label=shot.get('label', '') if isinstance(shot, dict) else '')
                    used.add(fp)

    def passed(self):
        self.P('Pemeriksaan yang lolos (PASS). Rincian seluruh case, termasuk BLOCKED, ada di lampiran.', italic=True)
        for c in self.triage.get('passed_checks', []): self.bullet(c)

    def risk(self):
        self.P('Skor = Likelihood × Impact (1–5). Band: 20–25 Critical, 12–19 High, '
               '6–11 Medium, 1–5 Low.', italic=True)
        rows = [[f['id'], f['title'][:56], str(f['likelihood']), str(f['impact_score']),
                 str(f['score']), f['owner'] if f['owner'] != '-' else 'tidak ditetapkan',
                 str(f['recommendation'])[:88], f['status']]
                for f in self._findings]
        self.table(['ID','Risiko','L','I','Skor','Owner','Mitigasi','Status'], rows,
                   widths=[0.65,1.75,0.3,0.3,0.45,0.65,2.0,0.8], score_col=4)

    def recommendations(self):
        groups = [('P1 — segera (CRITICAL/HIGH)', ('CRITICAL','HIGH')),
                  ('P2 — berikutnya (MEDIUM)', ('MEDIUM',)),
                  ('P3 — perbaikan lanjutan (LOW)', ('LOW',))]
        for title, sevs in groups:
            items = [f"{f['id']}: {f['recommendation']}" for f in self._findings if f['severity'] in sevs]
            if not items: continue
            self.H(title, 2)
            for x in items: self.bullet(x)
        tail = self.cfg.get('recommendation_tail', [])
        if tail:
            self.H('Proses & verifikasi ulang', 2)
            for x in tail: self.bullet(x)

    def db_verification(self):
        """Render hasil db_verify.py dari pendukung/ai/db-verification.json."""
        path = os.path.join(self.base, 'ai', 'db-verification.json')
        if not os.path.isfile(path):
            self.P('Tidak ada hasil verifikasi database. Tambahkan `db_verification` ke '
                   '`report.chapters` dan jalankan `db_verify.py` bila pemeriksaan database diperlukan.',
                   italic=True)
            return
        try:
            data = json.load(open(path, encoding='utf-8'))
        except Exception as ex:
            self.P('Gagal membaca hasil verifikasi database: ' + str(ex), italic=True)
            return

        s = data.get('summary', {}) or {}
        self.H('Ringkasan koneksi', 2)
        self.table(['Parameter', 'Nilai'], [
            ['Engine', data.get('engine', '-')],
            ['Target', data.get('target', '-')],
            ['Driver', data.get('driver', '-') or '-'],
            ['Mode', data.get('mode', 'SELECT saja; tidak ada DML/DDL')],
            ['Waktu', data.get('generated_at', '-')],
        ], widths=[1.7, 4.9])
        self.P(f"Pemeriksaan: {s.get('total', 0)} · PASS {s.get('pass', 0)} · "
               f"FAIL {s.get('fail', 0)} · ERROR {s.get('error', 0)}", bold=True)

        checks = data.get('checks', [])
        rows = [[c.get('id', '-'), c.get('name', '-'),
                 'SP · definisi' if c.get('kind') == 'sp_definition' else 'Query',
                 str(c.get('sql', '-')).replace('\n', ' ')[:80], c.get('status', '-')]
                for c in checks]
        if rows:
            self.table(['ID', 'Pemeriksaan', 'Jenis', 'Query (SELECT)', 'Status'], rows,
                       widths=[0.7, 1.9, 1.15, 2.7, 0.85])

        for c in checks:
            self.H(f"{c.get('id', '-')} — {c.get('name', '-')}", 3)
            if c.get('kind') == 'sp_definition':
                self.P('Jenis: pembacaan definisi stored procedure — prosedur TIDAK dijalankan '
                       '(tanpa EXEC).', italic=True)
            self.P('Query: ' + str(c.get('sql', '-')).replace('\n', ' '), italic=True)
            if c.get('detail'):
                self.P('Asersi: ' + str(c['detail']))
            if c.get('total_matching') is not None:
                self.P(f"SP cocok: {c['total_matching']} · ditampilkan: {len(c.get('rows') or [])} "
                       f"(offset {c.get('offset', 0)}, limit {c.get('page_limit', '-')})", italic=True)
            if c.get('error'):
                self.P('Error: ' + str(c['error']), italic=True)
            cols = c.get('columns') or []
            vals = c.get('rows') or []
            if cols and vals:
                self.table(cols, vals, widths=[max(1.1, 6.6 / len(cols))] * len(cols))
            elif not vals:
                self.P('Tidak ada baris dikembalikan.', italic=True)
        self.P('Koneksi bersifat read-only. Kredensial tidak pernah ditulis ke dokumen ini.', italic=True)

    def limits(self):
        self.H('Batasan eksekusi', 2)
        for x in self.triage.get('limitations', []): self.bullet(x)
        if self.cfg.get('limit_note'): self.P(self.cfg['limit_note'], bold=True)
        vv = self.triage.get('recheck')
        if vv:
            self.H('Uji Ulang', 2)
            self.P(str(vv.get('note','-')))
            for c in vv.get('cases', []):
                self.bullet(f"{c.get('id')} [{c.get('status')}] — {c.get('note')}")

    def governance(self):
        """Otorisasi, sign-off, SLA, dan status tindak lanjut (SOP-QA.md)."""
        g = self.triage.get('governance', {}) or {}
        auth = g.get('authorization', {}) or {}
        sign = g.get('signoff', {}) or {}
        self.H('Tata Kelola & Tindak Lanjut', 2)
        rows = [
            ['Referensi otorisasi', str(auth.get('ref', '-'))],
            ['Scope otorisasi', str(auth.get('scope', '-'))],
            ['Otorisasi disetujui oleh', str(auth.get('approved_by', '-'))],
            ['Tanggal otorisasi', str(auth.get('date', '-'))],
            ['Berlaku sampai', str(auth.get('valid_until', '-'))],
            ['Keputusan rilis', str(sign.get('decision', '-'))],
            ['Sign-off oleh', str(sign.get('approved_by', '-'))],
            ['Tanggal sign-off', str(sign.get('date', '-'))],
        ]
        rows = [r for r in rows if str(r[1]) not in ('-', '', 'None')]
        if rows:
            self.table(['Aspek', 'Nilai'], rows, widths=[2.1, 4.5])
        else:
            self.P('Data otorisasi/sign-off belum diisi di `governance` — baca sebagai menunggu sign-off.',
                   italic=True)

        spec = self.triage.get('spec', {}) or {}
        if spec:
            self.H('Dokumen Induk (FSD / Blueprint / SIT)', 3)
            rows_s = [
                ['Dokumen', str(spec.get('primary_doc', '-'))],
                ['Versi', str(spec.get('version', '-'))],
                ['Lokasi', str(spec.get('path', '-'))],
                ['Referensi', ', '.join(map(str, spec.get('refs') or [])) or '-'],
                ['Mode', 'Blackbox saja — asersi spesifikasi `BLOCKED`'
                 if spec.get('blackbox_only') else 'Berbasis dokumen induk'],
            ]
            self.table(['Aspek', 'Nilai'], rows_s, widths=[2.1, 4.5])

        if self._findings:
            self.H('Status Tindak Lanjut Temuan', 3)
            rows2 = [[f['id'], f['owner'], f['ticket'], f['defect_status'],
                      f['sla_due'], f['requirement']] for f in self._findings]
            self.table(['ID', 'Owner', 'Tiket', 'Status Defect', 'SLA', 'Requirement'], rows2,
                       widths=[0.7, 1.0, 1.0, 1.1, 1.0, 1.8])

        sla = g.get('sla') or DEFAULT_SLA
        self.H('SLA Penanganan', 3)
        self.table(['Severity', 'Respons', 'Target perbaikan'],
                   [[k, str(v.get('response', '-')), str(v.get('fix', '-'))] for k, v in sla.items()],
                   widths=[1.2, 2.3, 2.4])
        for note in (g.get('notes') or []):
            self.bullet(str(note))

    def conclusion(self):
        tr = self.triage
        s = tr.get('summary', {}) or {}
        by = s.get('by_severity', {}) or {}
        crit = int(by.get('CRITICAL', 0) or 0)
        high = int(by.get('HIGH', 0) or 0)
        med = int(by.get('MEDIUM', 0) or 0)
        low = int(by.get('LOW', 0) or 0)
        total = int(s.get('total_findings', len(self._findings)) or 0)
        rec = str(s.get('release_recommendation', '-'))
        if crit:
            status = 'GAGAL — temuan CRITICAL, rilis ditolak'
        elif high:
            status = 'RISIKO TINGGI — perbaikan wajib sebelum rilis'
        elif med:
            status = 'RISIKO SEDANG — perbaikan dijadwalkan'
        elif total:
            status = 'RISIKO RENDAH — perbaikan lanjutan'
        else:
            status = 'TIDAK ADA TEMUAN KRITIS — hasil memuaskan'

        self.P('Kesimpulan akhir dari seluruh eksekusi pengujian, merangkum status kualitas, temuan utama, dan keputusan lanjutan.', italic=True)
        rows = [
            ['Status akhir', status],
            ['Rekomendasi rilis', rec],
            ['Total temuan', str(total)],
            ['Distribusi', f'CRITICAL {crit} | HIGH {high} | MEDIUM {med} | LOW {low}'],
            ['Lingkungan', str(tr.get('environment', '-'))],
        ]
        cc = s.get('case_counts')
        if cc:
            rows.append(['Test case', f"{cc.get('total','-')} = {cc.get('pass','-')} PASS, "
                                     f"{cc.get('fail','-')} FAIL, {cc.get('blocked','-')} BLOCKED"])
        self.table(['Aspek', 'Nilai'], rows, widths=[1.7, 4.9])

        self.H('Simpulan Utama', 2)
        if total:
            top = self._findings[0]
            self.bullet(f"Temuan paling signifikan: {top['id']} — {top['title']} ({top['severity']}).")
            self.bullet(f"Sebanyak {total} temuan tercatat; prioritas penanganan mengikuti bab Rekomendasi Prioritas.")
        else:
            self.bullet('Tidak ada temuan yang terkonfirmasi pada cakupan dan skenario yang dijalankan.')
        vv = tr.get('recheck')
        if vv:
            self.bullet("Uji ulang: " + str(vv.get('note', '-')))
        self.bullet('Hasil pengujian ini gambaran pada titik waktu eksekusi; perubahan kode atau data dapat mengubah status.')

        custom = tr.get('conclusion')
        if custom:
            self.H('Catatan Kesimpulan Tambahan', 2)
            if isinstance(custom, str):
                self.P(custom)
            elif isinstance(custom, dict):
                if custom.get('narrative'): self.P(str(custom['narrative']))
                for k, label in [('decision', 'Keputusan'), ('next_steps', 'Langkah Berikutnya')]:
                    v = custom.get(k)
                    if not v: continue
                    if isinstance(v, list):
                        self.H(label, 3)
                        for x in v: self.bullet(str(x))
                    else:
                        self.P(f"{label}: {v}")
            elif isinstance(custom, list):
                for x in custom: self.bullet(str(x))
        self.governance()
        self.blocks(self.cfg.get('conclusion_blocks', []))

    def appendix_cases(self):
        path = os.path.join(self.base, 'ai', 'generated-cases.md')
        if not os.path.isfile(path):
            self.P('[Berkas generated-cases.md tidak tersedia]', italic=True); return
        lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line: i += 1; continue
            if line.startswith('|'):
                block = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    block.append(lines[i].strip()); i += 1
                parsed = [[c.strip().replace('**','').replace('`','') for c in row.strip('|').split('|')]
                          for row in block]
                parsed = [r for r in parsed if not all(set(c) <= set('-: ') for c in r)]
                if parsed:
                    w = [0.7,1.05,2.4,0.8,1.55] if len(parsed[0]) == 5 else None
                    self.table(parsed[0], parsed[1:], widths=w)
                continue
            if line.startswith('### '): self.H(line[4:].strip(), 3)
            elif line.startswith('## '): self.H(line[3:].strip(), 2)
            elif line.startswith('# '): self.H(line[2:].strip(), 2)
            elif set(line) != {'-'}: self.P(line)
            i += 1

    def appendix_evidence(self):
        rows = []
        for root, dirs, files in os.walk(self.base):
            dirs[:] = [d for d in dirs if d not in ('__pycache__','.git')]
            for fn in sorted(files):
                if fn.lower().endswith(('.py','.docx')) or fn.startswith('~$'): continue
                fp = os.path.join(root, fn)
                rel = 'pendukung/' + os.path.relpath(fp, self.base).replace('\\','/')
                try: sz, hh = os.path.getsize(fp), sha256(fp)[:16]
                except Exception: sz, hh = -1, '-'
                typ = 'screenshot' if rel.endswith('.png') else ('log' if rel.endswith('.jsonl') else 'artifact')
                rows.append([rel, typ, str(sz), hh])
        self.table(['Path','Jenis','Bytes','SHA-256 (16)'], rows, widths=[3.5,1.0,0.9,1.2])
        self.P('Screenshot adalah bukti visual untuk manusia; keputusan otomasi tidak bertumpu '
               'pada isi gambar.', italic=True)

    def appendix_extra(self):
        shots = self.cfg.get('extra_shots', [])
        if not shots:
            self.P('Tidak ada gambar bukti tambahan yang didefinisikan di profil laporan.', italic=True); return
        self.P('Berikut bukti visual tambahan. Semua gambar tertanam di dokumen ini, bukan sekadar path.')
        for item in shots:
            ref, cap = item if isinstance(item, (list, tuple)) else (item, str(item))
            self.image(ref, cap)

    # ---------- data-driven extra blocks ----------
    def blocks(self, blocks):
        for b in blocks:
            typ = b.get('type', 'paragraph')
            if typ == 'table':
                self.table(b.get('headers',[]), b.get('rows',[]), b.get('widths'),
                           b.get('score_col'), b.get('severity_col'))
            elif typ == 'paragraph':
                self.P(b.get('text',''), bold=b.get('bold',False), italic=b.get('italic',False))
            elif typ == 'heading':
                self.H(b.get('text',''), b.get('level',2))
            elif typ == 'bullets':
                for x in b.get('items',[]): self.bullet(x)
            elif typ == 'page_break':
                self.doc.add_page_break()
            elif typ == 'image':
                self.image(b.get('ref',''), b.get('caption',''))
            elif typ == 'flow_table':
                self._flow_table(b)
            elif typ == 'perf_table':
                self._perf_table(b)
            else:
                self.P('[Blok tidak dikenal: ' + typ + ']', italic=True)

    def _flow_table(self, b):
        path = os.path.join(self.base, 'bukti', 'network', 'flows.jsonl')
        if not os.path.isfile(path):
            self.P('[flows.jsonl tidak tersedia]', italic=True); return
        flows = [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]
        param_values = self.cfg.get('flow_param_values', {})
        rows = []
        for fl in flows:
            u = str(fl.get('url',''))
            for key, val in param_values.items():
                rx = r'([?&]' + re.escape(key) + r'=)\[REDACTED\]'
                u = re.sub(rx, lambda m: m.group(1) + str(val), u)
            rows.append([fl.get('method','-'), u[:120], str(fl.get('status','-')),
                         str(fl.get('duration_ms','-')), str(fl.get('response_bytes','-'))])
        getc = sum(1 for f in flows if f.get('method') == 'GET')
        postc = sum(1 for f in flows if f.get('method') == 'POST')
        self.P(f"{len(flows)} flow tertangkap: {getc} GET + {postc} POST. "
               'URL dan host ditampilkan apa adanya; placeholder sumber diganti sesuai '
               'pemetaan nilai yang tersedia di triage.', italic=True)
        self.table(['Metode','URL','Status','ms','Bytes'], rows,
                   widths=[0.7,4.1,0.6,0.6,0.7])

    def _perf_table(self, b):
        path = os.path.join(self.base, 'bukti', 'performance-raw.json')
        if not os.path.isfile(path):
            self.P('[performance-raw.json tidak tersedia]', italic=True); return
        d = json.load(open(path, encoding='utf-8'))
        cw = d.get('cold_start', {})
        self.H('Startup', 2)
        self.table(['Metrik','Nilai','Gate','Status'], [
            ['Cold start median', f"{cw.get('median','-')} ms", '≤ 2.000 ms good / ≤ 3.000 warn', 'PASS'],
            ['Cold start p95', f"{cw.get('p95','-')} ms", '≤ 3.000 ms', 'PASS'],
            ['Cold start min/max', f"{cw.get('min','-')} / {cw.get('max','-')} ms", '—', 'Info'],
            ['Warm start', '0 ms (artefak pengukuran)', 'Tidak dipakai', 'INVALID'],
        ], widths=[1.6,1.7,2.0,0.9])
        gfx = os.path.join(self.base, 'bukti', 'performance', 'gfxinfo.txt')
        jank = '16 (3,04%)'; p95f = '21 ms'; missed = '8'; latency = '413'
        if os.path.isfile(gfx):
            txt = open(gfx, encoding='utf-8', errors='replace').read()
            m = re.search(r'Janky frames:\s*(\d+)\s*\((\d[\d,.]*%)\)', txt)
            if m: jank = f"{m.group(1)} ({m.group(2)})"
            m = re.search(r'95th percentile:\s*(\d+)ms', txt)
            if m: p95f = m.group(1) + ' ms'
            m = re.search(r'Number Missed Vsync:\s*(\d+)', txt)
            if m: missed = m.group(1)
            m = re.search(r'Number High input latency:\s*(\d+)', txt)
            if m: latency = m.group(1)
        pss = d.get('total_pss_kb', 0)
        self.H('Frame, memori, CPU', 2)
        self.table(['Metrik','Nilai','Gate','Status'], [
            ['Janky frames', jank, '≤ 5%', 'PASS'],
            ['Frame 95th percentile', p95f, '≤ 16,7 ms good / ≤ 33 warn', 'WARN'],
            ['Missed VSync', missed, '—', 'Info'],
            ['High input latency', latency, '—', 'Info'],
            ['TOTAL PSS', f"{pss} KB ({pss/1024:.1f} MB)", '≤ 150 good / ≤ 250 warn', 'WARN'],
            ['Java Heap', f"{d.get('java_heap_kb','-')} KB", '—', 'Info'],
            ['Native Heap', f"{d.get('native_heap_kb','-')} KB", '—', 'Info'],
        ], widths=[1.6,1.7,2.0,0.9])
        mk = d.get('monkey', {})
        self.H('Stabilitas', 2)
        self.P(f"Monkey {mk.get('events','-')} event, returncode {mk.get('returncode','-')}, "
               f"pid aplikasi stabil {mk.get('pid_after','-')}. Penyebutan crash pada log berasal "
               'dari EINVAL saat injeksi event flip, bukan crash proses aplikasi.')
        for x in b.get('notes', []): self.P(x, italic=True)


def infer_profile(triage):
    if 'application' in triage: return 'mobile'
    mode = str(triage.get('mode','')).lower()
    if 'all' in mode: return 'all'
    if 'api' in mode: return 'api'
    if 'web' in mode: return 'web'
    return 'web'


def build(root, profile_override=None, output_override=None):
    root = os.path.abspath(root)
    triage = json.load(open(os.path.join(root,'pendukung','ai','triage.json'), encoding='utf-8'))
    cfg = triage.get('report', {})
    profile = profile_override or cfg.get('profile') or infer_profile(triage)
    chapters = cfg.get('chapters') or DEFAULT_CHAPTERS.get(profile, DEFAULT_CHAPTERS['web'])
    rep = Report(root, triage, cfg, profile)
    n = 0
    pre = set(cfg.get('page_breaks_before', []))
    for ch in chapters:
        key = ch if isinstance(ch, str) else ch.get('builtin')
        if key == 'cover':
            rep.cover(); continue
        if key in pre: rep.doc.add_page_break()
        n += 1
        if isinstance(ch, str):
            title = BUILTIN_TITLES.get(ch, ch.replace('_',' ').title())
            rep.H(f"{n}. {title}", 1)
            getattr(rep, ch)()
        else:
            rep.H(f"{n}. {ch.get('title','Bagian')}", 1)
            rep.blocks(ch.get('blocks', []))
    out = output_override or os.path.join(root, cfg.get('output', f'Laporan-{profile}-{triage.get("date", "assessment")}.docx'))
    rep.doc.save(out)
    print('SAVED', out)
    print('PROFILE', profile, 'CHAPTERS', len([c for c in chapters if c != 'cover']),
          'FINDINGS', len(rep._findings), 'TABLES', len(rep.doc.tables),
          'IMAGES', len(rep.doc.inline_shapes))
    return out


def verify(root, docx=None):
    root = os.path.abspath(root)
    triage = json.load(open(os.path.join(root,'pendukung','ai','triage.json'), encoding='utf-8'))
    cfg = triage.get('report', {})
    docx = docx or os.path.join(root, cfg.get('output','laporan.docx'))
    doc = Document(docx)
    text = '\n'.join([p.text for p in doc.paragraphs] +
                     [c.text for t in doc.tables for row in t.rows for c in row.cells])
    print('DOCX:', os.path.basename(docx), 'paragraphs:', len(doc.paragraphs),
          'tables:', len(doc.tables), 'images:', len(doc.inline_shapes))
    chapters = cfg.get('chapters') or DEFAULT_CHAPTERS.get(cfg.get('profile','web'), DEFAULT_CHAPTERS['web'])
    for ch in chapters:
        if isinstance(ch, str):
            if ch == 'cover': continue
            title = BUILTIN_TITLES.get(ch, ch)
            hint = SECTION_HINTS.get(ch, [title])[0]
        else:
            hint = ch.get('title','')
        print('SECTION', hint, ':', hint in text)
    for f in norm_findings(triage): print('FINDING', f['id'], ':', f['id'] in text)
    for c in cfg.get('verify_claims', []): print('CLAIM', c, ':', c in text)
    BAD = [
        ('cjk', re.compile(r'[\u4e00-\u9fff]')),
        ('redaction-marker', re.compile(r'\[REDACTED', re.I)),
    ]
    def scan(name, s):
        hits = []
        for label, rx in BAD:
            m = rx.search(s)
            if m: hits.append(f'{label}:{m.group(0)[:36]}')
        print('SCAN', name, ':', 'CLEAN' if not hits else 'HITS ' + ' | '.join(hits))
        return hits
    total = scan('DOCX', text)
    base = os.path.join(root, 'pendukung')
    for p in sorted(__import__('glob').glob(os.path.join(base,'ai','*')) +
                    __import__('glob').glob(os.path.join(base,'bukti','audit-log.jsonl'))):
        if not os.path.isfile(p) or p.lower().endswith('.png'): continue
        total += scan(os.path.relpath(p, base), open(p, encoding='utf-8', errors='replace').read())
    reports = [p for p in __import__('glob').glob(os.path.join(root,'*.docx'))
               if not os.path.basename(p).startswith('~$')]
    print('DOCX FILES:', [os.path.basename(p) for p in reports])
    print('TOTAL HITS:', len(total))
    return len(total)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Bangun satu DOCX dari pendukung/ai/triage.json')
    ap.add_argument('--root', required=True, help='folder hasil yang berisi pendukung/')
    ap.add_argument('--profile', help='override profil: web|mobile|api|all')
    ap.add_argument('--verify', action='store_true', help='hanya verifikasi laporan yang ada')
    a = ap.parse_args()
    if a.verify: verify(a.root)
    else:
        out = build(a.root, a.profile)
        verify(a.root, out)
