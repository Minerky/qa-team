# -*- coding: utf-8 -*-
"""Kit render laporan Bug Hunter & Vulnerability Assessment generik.

Satu source of truth: pendukung/ai/triage.json.
Target menentukan isi lewat blok `report` di triage (profil, bab, tabel tambahan,
gambar bukti). Kit ini dirancang untuk laporan Bug Bounty, Vulnerability Assessment,
Reconnaissance, Chaos / Monkey Testing, dan Status Cleanup Terverifikasi.
"""
import os, re, json, hashlib, argparse
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Renderer sengaja TIDAK menyensor nilai. Nilai yang tersedia di artefak tampil
# apa adanya di DOCX; nilai yang tidak ada ditulis `(...)` di triage.json.
def R(text):
    """Identity renderer — pertahankan nilai apa adanya dari triage/artefak."""
    return str(text)

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

SEV_LI = {'CRITICAL': (5, 5), 'HIGH': (4, 4), 'MEDIUM': (3, 3), 'LOW': (2, 2), 'INFO': (1, 1)}
SEV_FILL = {'CRITICAL': 'B00000', 'HIGH': 'C05000', 'MEDIUM': '8A6D00', 'LOW': '336633', 'INFO': '2B5B84'}
SEV_RGB = {'CRITICAL': RGBColor(0xB0,0x00,0x00), 'HIGH': RGBColor(0xC0,0x50,0x00),
           'MEDIUM': RGBColor(0x8A,0x6D,0x00), 'LOW': RGBColor(0x33,0x66,0x33),
           'INFO': RGBColor(0x2B,0x5B,0x84)}

_FULL = ['cover','executive','scope','method','environment',
         'waf_analysis','recon','subdomain_takeover',
         'jwt_analysis','oauth_analysis','twofa_analysis',
         'api_versions','blind_findings','business_logic','cache_poisoning',
         'smuggling','injection_advanced','client_side','supply_chain','mobile_deeplink',
         'cve_matches','kill_chains','findings','chaos',
         'risk','recommendations','limits','conclusion',
         'appendix_cases','appendix_submissions','appendix_evidence','appendix_extra']

DEFAULT_CHAPTERS = {
    'bughunt': _FULL, 'web': _FULL, 'apk': _FULL, 'all': _FULL,
}

BUILTIN_TITLES = {
    'executive':          'Ringkasan Eksekutif & Distribusi Risiko',
    'scope':              'Scope & Rules of Engagement',
    'method':             'Metodologi Pengujian',
    'environment':        'Target & Lingkungan Pengujian',
    'waf_analysis':       'WAF Detection & Bypass Analysis',
    'recon':              'Reconnaissance & Attack Surface Mapping',
    'subdomain_takeover': 'Subdomain Takeover Detection',
    'jwt_analysis':       'JWT Security Analysis',
    'oauth_analysis':     'OAuth 2.0 / OIDC Abuse Testing',
    'twofa_analysis':     '2FA / OTP Bypass Testing',
    'api_versions':       'API Versioning Abuse',
    'blind_findings':     'Blind Vulnerability Detection (OOB)',
    'business_logic':     'Business Logic Testing',
    'cache_poisoning':    'Cache Poisoning & Cache Deception',
    'smuggling':          'HTTP Request Smuggling (CL.TE / TE.CL)',
    'injection_advanced': 'Advanced Injection — SSTI, XXE, Prototype Pollution, LFI, Clickjacking',
    'supply_chain':       'Dependency Confusion & Supply Chain Attack',
    'mobile_deeplink':    'Mobile Deep Link & Intent Hijacking',
    'client_side':        'Client-Side Attacks — CORS, DNS Rebinding',
    'cve_matches':        'CVE Matching dari Tech Fingerprint',
    'kill_chains':        'Kill Chain & Exploit Chain Analysis',
    'findings':           'Temuan Kerentanan & Bukti PoC',
    'passed':             'Pemeriksaan yang Lolos',
    'chaos':              'Pengujian Chaos / Monkey & Status Cleanup',
    'risk':               'Risk Register & Matriks Risiko',
    'recommendations':    'Rekomendasi Remediasi Prioritas',
    'db_verification':    'Verifikasi Database (Read-Only)',
    'limits':             'Batasan Pengujian & Status',
    'conclusion':         'Kesimpulan & Rekomendasi Akhir',
    'appendix_cases':     'Lampiran — Daftar Skenario Uji',
    'appendix_submissions': 'Lampiran — Format Submission Bug Bounty (HackerOne & Bugcrowd)',
    'appendix_evidence':  'Lampiran — Inventaris Bukti & Traffic',
    'appendix_extra':     'Lampiran — Bukti Visual / Screenshot',
}

SECTION_HINTS = {
    'scope': ['Scope & Rules'], 'method': ['Metodologi'], 'environment': ['Target & Lingkungan'],
    'waf_analysis': ['WAF Detection'], 'recon': ['Reconnaissance'],
    'subdomain_takeover': ['Subdomain Takeover'],
    'jwt_analysis': ['JWT Security'], 'oauth_analysis': ['OAuth'],
    'twofa_analysis': ['2FA'], 'api_versions': ['API Versioning'],
    'blind_findings': ['Blind Vulnerability'], 'business_logic': ['Business Logic'],
    'cache_poisoning': ['Cache Poisoning'],
    'smuggling': ['HTTP Request Smuggling'],
    'injection_advanced': ['Advanced Injection'],
    'supply_chain': ['Supply Chain'],
    'mobile_deeplink': ['Mobile Deep Link'],
    'client_side': ['Client-Side'],
    'cve_matches': ['CVE Matching'], 'kill_chains': ['Kill Chain'],
    'findings': ['Temuan Kerentanan'], 'chaos': ['Pengujian Chaos'],
    'risk': ['Risk Register'], 'recommendations': ['Rekomendasi Remediasi'],
    'db_verification': ['Verifikasi Database'],
    'limits': ['Batasan Pengujian'], 'conclusion': ['Kesimpulan'], 'appendix_cases': ['Daftar Skenario Uji'],
    'appendix_submissions': ['Format Submission', 'Submission Bug Bounty'],
    'appendix_evidence': ['Inventaris Bukti'], 'appendix_extra': ['Bukti Visual'],
}


def norm_shots(finding):
    """Screenshot PoC + anotasi merah. Format lama (string) dan baru (dict) didukung.

      "shots": [{"ref": "file.png",
                 "highlight": {"type": "circle", "x": 0.6, "y": 0.3, "w": 0.2, "h": 0.15},
                 "label": "Area temuan"}]
    Koordinat x/y/w/h relatif (0–1) terhadap gambar; nilai >1 dibaca piksel.
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
            'cvss': f.get('cvss', '-'), 'cwe': f.get('cwe', '-'),
            'likelihood': likelihood, 'impact_score': impact_score, 'score': score,
            'expected': f.get('expected', '-'), 'actual': f.get('actual', '-'),
            'business': business, 'recommendation': f.get('recommendation') or f.get('rec') or '-',
            'steps': f.get('steps') or f.get('poc_steps') or [],
            'poc_snippet': f.get('poc_snippet', ''),
            'chain': f.get('chain') or [], 'evidence': ev, 'confidence': f.get('confidence', '-'),
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

    def _setup(self):
        sec = self.doc.sections[0]
        sec.top_margin = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin = Inches(0.8)
        sec.right_margin = Inches(0.8)
        sec.page_width = Inches(8.27)
        sec.page_height = Inches(11.69)
        self._footer(sec)

        norm = self.doc.styles['Normal']
        norm.font.name = 'Calibri'
        norm.font.size = Pt(10)
        norm.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        norm.paragraph_format.line_spacing = 1.15
        norm.paragraph_format.space_after = Pt(4)

        for lvl, sz, col in [(1,16,RGBColor(0x0E,0x2A,0x47)),(2,13,RGBColor(0x1B,0x36,0x5D)),(3,11,RGBColor(0x2C,0x4D,0x75))]:
            try:
                st = self.doc.styles[f'Heading {lvl}']
                st.font.name = 'Calibri'
                st.font.size = Pt(sz)
                st.font.bold = True
                st.font.color.rgb = col
                st.paragraph_format.space_before = Pt(10)
                st.paragraph_format.space_after = Pt(3)
            except Exception:
                pass

    def _footer(self, sec):
        ft = sec.footer; p = ft.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.text = f"{self.triage.get('target', 'Target')} — Bug Hunter & Vulnerability Assessment | Hal. "
        self._page_field(p)

    @staticmethod
    def _shade(cell, fill):
        tcPr = cell._tc.get_or_add_tcPr()
        for e in list(tcPr):
            if e.tag.endswith('shd'): tcPr.remove(e)
        tcPr.append(OxmlElement('w:shd', {qn('w:val'):'clear', qn('w:color'):'auto', qn('w:fill'):fill}))

    @staticmethod
    def _margins(cell, top=70, start=100, bottom=70, end=100):
        tcPr = cell._tc.get_or_add_tcPr()
        for e in list(tcPr):
            if e.tag.endswith('tcMar'): tcPr.remove(e)
        tcMar = OxmlElement('w:tcMar')
        for k, v in [('top',top),('left',start),('bottom',bottom),('right',end)]:
            m = OxmlElement(f'w:{k}', {qn('w:w'):str(v), qn('w:type'):'dxa'})
            tcMar.append(m)
        tcPr.append(tcMar)

    @staticmethod
    def _repeat(row):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement('w:tblHeader'))
        trPr.append(OxmlElement('w:cantSplit'))

    @staticmethod
    def _borders(t):
        tblPr = t._tbl.tblPr
        for e in list(tblPr):
            if e.tag.endswith('tblBorders'): tblPr.remove(e)
        b = OxmlElement('w:tblBorders')
        for side in ['top','left','bottom','right','insideH','insideV']:
            b.append(OxmlElement(f'w:{side}', {qn('w:val'):'single', qn('w:sz'):'4', qn('w:space'):'0', qn('w:color'):'D6DCE5'}))
        tblPr.append(b)

    @staticmethod
    def _page_field(p):
        r = p.add_run()
        fldChar1 = OxmlElement('w:fldChar'); fldChar1.set(qn('w:fldCharType'), 'begin')
        instrText = OxmlElement('w:instrText'); instrText.set(qn('xml:space'), 'preserve'); instrText.text = "PAGE"
        fldChar2 = OxmlElement('w:fldChar'); fldChar2.set(qn('w:fldCharType'), 'separate')
        fldChar3 = OxmlElement('w:fldChar'); fldChar3.set(qn('w:fldCharType'), 'end')
        r._r.append(fldChar1); r._r.append(instrText); r._r.append(fldChar2); r._r.append(fldChar3)

    @staticmethod
    def _rule(p, color='C9D3DF', size='6'):
        pBdr = OxmlElement('w:pBdr')
        bot = OxmlElement('w:bottom', {qn('w:val'):'single', qn('w:sz'):size, qn('w:space'):'4', qn('w:color'):color})
        pBdr.append(bot)
        p._p.get_or_add_pPr().append(pBdr)

    def P(self, text='', bold=False, italic=False, size=None):
        p = self.doc.add_paragraph()
        r = p.add_run(R(text))
        r.bold = bold; r.italic = italic
        if size: r.font.size = Pt(size)
        return p

    def H(self, text, level=1):
        p = self.doc.add_heading(level=level)
        r = p.add_run(R(text))
        r.bold = True
        return p

    def spacer(self, pt=4):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(pt)
        p.paragraph_format.space_after = Pt(0)
        return p

    def table(self, headers, rows, widths=None, score_col=None, severity_col=None):
        t = self.doc.add_table(rows=len(rows)+1, cols=len(headers))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        self._borders(t)
        self._repeat(t.rows[0])
        hdr = t.rows[0]
        for i, h in enumerate(headers):
            c = hdr.cells[i]
            c.text = R(str(h))
            self._shade(c, '1B365D')
            self._margins(c, 80, 100, 80, 100)
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.bold = True; r.font.color.rgb = RGBColor(0xFF,0xFF,0xFF); r.font.size = Pt(9.5)
        for r_idx, row in enumerate(rows):
            tr = t.rows[r_idx+1]
            bg = 'F4F7FA' if (r_idx % 2 == 1) else 'FFFFFF'
            for c_idx, val in enumerate(row):
                c = tr.cells[c_idx]
                c.text = R(str(val))
                self._shade(c, bg)
                self._margins(c, 55, 90, 55, 90)
                c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                p = c.paragraphs[0]
                for r in p.runs: r.font.size = Pt(9)
                if severity_col is not None and c_idx == severity_col:
                    s = str(val).upper()
                    if s in SEV_FILL:
                        self._shade(c, SEV_FILL[s])
                        for r in p.runs:
                            r.font.bold = True
                            r.font.color.rgb = RGBColor(0xFF,0xFF,0xFF)
                if score_col is not None and c_idx == score_col:
                    try:
                        sc = int(val)
                        if sc >= 20: fill = SEV_FILL['CRITICAL']
                        elif sc >= 12: fill = SEV_FILL['HIGH']
                        elif sc >= 6: fill = SEV_FILL['MEDIUM']
                        else: fill = SEV_FILL['LOW']
                        self._shade(c, fill)
                        for r in p.runs:
                            r.font.bold = True
                            r.font.color.rgb = RGBColor(0xFF,0xFF,0xFF)
                    except Exception:
                        pass
        if widths:
            for row in t.rows:
                for idx, w in enumerate(widths):
                    if idx < len(row.cells): row.cells[idx].width = Inches(w)
        self.doc.add_paragraph()
        return t

    def bullet(self, text):
        p = self.doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(2)
        p.add_run(R(text))
        return p

    def banner(self, text, fill='8A6D00', size=11):
        t = self.doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = t.rows[0].cells[0]
        c.width = Inches(6.67)
        self._shade(c, fill)
        self._margins(c, 100, 140, 100, 140)
        p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(R(text))
        r.font.bold = True; r.font.size = Pt(size); r.font.color.rgb = RGBColor(0xFF,0xFF,0xFF)
        self.doc.add_paragraph()

    def resolve_image(self, ref):
        candidates = [
            ref,
            os.path.join(self.base, 'bukti', ref),
            os.path.join(self.base, 'bukti', 'screenshots', ref),
            os.path.join(self.base, 'screenshots', ref),
            os.path.join(self.base, ref),
            os.path.join(self.root, ref),
        ]
        for c in candidates:
            if c and os.path.isfile(c): return c
        bn = os.path.basename(ref)
        for sub in ['bukti', os.path.join('bukti', 'screenshots'), 'screenshots', '.']:
            d = os.path.join(self.base, sub)
            if os.path.isdir(d):
                p = os.path.join(d, bn)
                if os.path.isfile(p): return p
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
        r = p.add_run(R(cfg.get('title') or f"LAPORAN BUG HUNTER & VULNERABILITY ASSESSMENT\n{tr.get('target','-')}"))
        r.font.size = Pt(20); r.font.bold = True; r.font.color.rgb = RGBColor(0x0E,0x2A,0x47)

        sub = cfg.get('subtitle') or f"Penilaian Keamanan Otomatis, PoC Kerentanan, dan Chaos Testing"
        p2 = self.doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r2 = p2.add_run(R(sub))
        r2.font.size = Pt(12); r2.font.italic = True; r2.font.color.rgb = RGBColor(0x55,0x55,0x55)
        self._rule(p2, color='0E2A47', size='12')
        self.spacer(14)

        rows = self._cover_fields()
        self.table(['Parameter', 'Nilai'], rows, widths=[2.2, 4.4])
        self.spacer(10)

        notes = cfg.get('cover_notes') or [
            "Laporan ini menyajikan hasil reconnaissance, temuan kerentanan dengan pembuktian konsep (PoC), hasil pengujian chaos / monkey testing, serta status verifikasi pembersihan (cleanup) pasca-uji.",
            "Semua nilai aktual yang ditemukan di artefak ditampilkan apa adanya. Nilai yang tidak tersedia ditulis `(...)`."
        ]
        for note in notes:
            self.P(note, italic=True, size=9)
        self.doc.add_page_break()

    def _cover_fields(self):
        tr = self.triage
        v = tr.get('verdict') or tr.get('summary', {}).get('verdict', '-')
        rows = [
            ['Target', tr.get('target', '-')],
            ['Tanggal Pengujian', tr.get('date') or tr.get('generated_at', '-')],
            ['Profil Pengujian', self.profile.upper()],
            ['Status / Rekomendasi Rilis', str(v)],
            ['Klasifikasi Dokumen', 'Confidential — Vulnerability Assessment'],
            ['Referensi Tiket / Program', str(tr.get('ticket_ref', 'Bug Bounty Assessment'))]
        ]
        if 'application' in tr:
            app = tr['application']
            rows.insert(1, ['Aplikasi Target', f"{app.get('name','-')} v{app.get('version','-')} ({app.get('package','-')})"])
        return rows

    def executive(self):
        s = self.triage.get('summary', {})
        tot = s.get('total_findings', len(self._findings))
        by_sev = s.get('by_severity', {})
        v = self.triage.get('verdict') or s.get('verdict', '-')

        fill = 'B00000' if ('REJECT' in str(v) or 'DO_NOT' in str(v) or by_sev.get('CRITICAL',0)>0) else ('C05000' if by_sev.get('HIGH',0)>0 else '336633')
        self.banner(f"HASIL AKHIR: {v}", fill=fill, size=13)

        self.H('Distribusi Kerentanan Berdasarkan Tingkat Keparahan', 2)
        rows = [
            ['CRITICAL', str(by_sev.get('CRITICAL', 0)), 'Remediasi mendesak (P1)', 'Eksploitasi langsung dengan dampak masif'],
            ['HIGH',     str(by_sev.get('HIGH', 0)),     'Remediasi prioritas tinggi (P1)', 'Dampak signifikan terhadap integritas atau kerahasiaan'],
            ['MEDIUM',   str(by_sev.get('MEDIUM', 0)),   'Perbaikan pada sprint aktif (P2)', 'Kelemahan konfigurasi / akses terkontrol'],
            ['LOW',      str(by_sev.get('LOW', 0)),      'Perbaikan terjadwal (P3)', 'Penyimpangan best-practice / risiko minimal'],
            ['INFO',     str(by_sev.get('INFO', 0)),     'Informasional', 'Temuan observasi konfigurasi atau arsitektur'],
            ['TOTAL',    str(tot),                       '-', 'Seluruh temuan teridentifikasi']
        ]
        self.table(['Tingkat Keparahan', 'Jumlah', 'Tindakan', 'Definisi'], rows,
                   widths=[1.5, 0.8, 2.0, 2.3], severity_col=0)

        self.blocks(self.cfg.get('executive_blocks', []))

    def scope(self):
        tr = self.triage
        sc = tr.get('scope', {})
        in_scope = sc.get('in_scope', [tr.get('target', '-')])
        out_scope = sc.get('out_of_scope', ['Host di luar daftar yang ditentukan', 'Serangan Denial of Service (DoS/DDoS)', 'Perusakan data permanen tanpa rollback'])

        rows = [
            ['Target Terotorisasi', '\n'.join(in_scope) if isinstance(in_scope, list) else str(in_scope)],
            ['Batasan / Out-of-Scope', '\n'.join(out_scope) if isinstance(out_scope, list) else str(out_scope)],
            ['Rules of Engagement', 'Non-destruktif default; probe verifikasi celah; pengujian resiliensi dengan pembersihan otomatis.'],
            ['Stop Condition', 'Hentikan eksplorasi bila terjadi instabilitas sistem target yang tidak terduga.'],
        ]
        self.table(['Aspek Scope', 'Ketentuan'], rows, widths=[1.8, 4.8])
        self.blocks(self.cfg.get('scope_blocks', []))

    def method(self):
        rows = self.cfg.get('method_rows') or [
            ['Fase', 'Alat & Teknik', 'Bukti / Output'],
            ['Reconnaissance', 'DNS, header inspection, JS/manifest parse, secret hunting', 'Daftar endpoint & secret scan'],
            ['Vulnerability Assessment', 'Playwright browser, ADB, static analysis, passive flow capture', 'Log interaksi & request capture'],
            ['Chaos / Monkey Testing', 'Input fuzzing, unexpected method/type, monkey random UI stress', 'Resilience log & error responses'],
            ['Cleanup & Verification', 'Automated reset cookies/session, adb shell cleanup, DB record teardown', 'Audit log pembersihan terverifikasi'],
            ['Reporting', 'Satu source of truth triage.json -> satu DOCX mandiri', 'Dokumen laporan ini'],
        ]
        if rows and len(rows[0]) == 2:
            self.table(rows[0], rows[1:], widths=[1.8, 4.8])
        else:
            self.table(rows[0], rows[1:], widths=[1.5, 2.5, 2.6])
        self.blocks(self.cfg.get('method_blocks', []))

    def environment(self):
        tr = self.triage; acc = tr.get('test_account', {})
        rows = [['Komponen', 'Keterangan'],
                ['Target Pengujian', tr.get('target', '-')],
                ['Environment', tr.get('environment', '-')],
                ['Otorisasi', tr.get('authorization', '-')],
                ['Akun Uji', acc.get('identity', '(...)')],
                ['Role Akun', acc.get('role', '(...)')],
                ['Sumber Akun', acc.get('source', '(...)')],
                ['Kredensial / Token', ' / '.join(filter(None, [str(acc.get('password','')), str(acc.get('token',''))])) or '(...)']]
        if 'application' in tr:
            app = tr['application']
            rows.insert(1, ['Nama Aplikasi', app.get('name', '-')])
            rows.insert(2, ['Versi & Build', app.get('version', '-')])
            rows.insert(3, ['Package ID', app.get('package', '-')])
        self.table(rows[0], rows[1:], widths=[1.8, 4.8])
        self.blocks(self.cfg.get('environment_blocks', []))

    def waf_analysis(self):
        w = self.triage.get('waf', {})
        detected = w.get('detected', False)
        waf_type = w.get('type', '(tidak terdeteksi)')
        if not detected:
            self.P('Tidak ada WAF yang terdeteksi pada target. Semua probe dikirim langsung tanpa bypass.', italic=True)
            return
        self.banner(f"WAF TERDETEKSI: {waf_type}", fill='1B365D', size=11)
        self.P(f"Tipe WAF yang teridentifikasi: {waf_type}. Teknik bypass diuji secara otomatis sebelum setiap probe kerentanan.", italic=True)
        bypass_ok = w.get('bypass_success', [])
        bypass_fail = w.get('bypass_failed', [])
        rows = (
            [['BERHASIL', b] for b in bypass_ok] +
            [['GAGAL', b] for b in bypass_fail]
        )
        if rows:
            self.table(['Hasil', 'Teknik Bypass'], rows, widths=[1.2, 5.4])
        self.blocks(self.cfg.get('waf_blocks', []))

    def jwt_analysis(self):
        jwts = self.triage.get('jwt_analysis', [])
        if not jwts:
            self.P('Tidak ada JWT yang ditemukan atau dianalisis pada sesi ini.', italic=True)
            return
        self.P('Setiap JWT yang ditemukan di header, cookie, atau response body dianalisis: decode claims, algorithm check, secret bruteforce, dan claim tampering.', italic=True)
        for j in jwts:
            sev = str(j.get('severity', 'HIGH')).upper()
            h = self.H(f"{j.get('id','-')} — {j.get('location','-')}", 2)
            for r in h.runs:
                if sev in SEV_RGB: r.font.color.rgb = SEV_RGB[sev]
            meta = [
                ['Lokasi', j.get('location', '-')],
                ['Algoritma', j.get('algorithm', '-')],
                ['Kerentanan', j.get('vulnerability', '-')],
                ['Severity', sev],
                ['Eksploit Berhasil', j.get('exploit', '-')],
            ]
            self.table(['Parameter', 'Nilai'], meta, widths=[1.8, 4.8])
            claims = j.get('claims', {})
            if claims:
                self.P('Decoded Claims:', bold=True)
                for k, v in claims.items():
                    self.bullet(f"{k}: {v}")

    def cve_matches(self):
        cves = self.triage.get('cve_matches', [])
        if not cves:
            self.P('Tidak ada CVE yang cocok ditemukan untuk komponen yang teridentifikasi.', italic=True)
            return
        self.P('Komponen dan versi yang teridentifikasi saat reconnaissance dicocokkan dengan database CVE NIST NVD. Tabel berikut menampilkan CVE dengan CVSS ≥ 7.0.', italic=True)
        rows = [
            [c.get('component', '-'),
             c.get('cve', '-'),
             str(c.get('cvss', '-')),
             c.get('description', '-')[:80],
             'YA' if c.get('likely_vulnerable') else 'PERLU VERIFIKASI']
            for c in cves
        ]
        self.table(
            ['Komponen', 'CVE', 'CVSS', 'Deskripsi', 'Kemungkinan Rentan'],
            rows, widths=[1.5, 1.2, 0.6, 2.9, 1.4]
        )
        self.blocks(self.cfg.get('cve_blocks', []))

    def subdomain_takeover(self):
        items = self.triage.get('subdomain_takeover', [])
        if not items:
            self.P('Tidak ada kandidat subdomain takeover yang terdeteksi.', italic=True)
            return
        self.P('Subdomain dengan CNAME pointing ke layanan eksternal yang sudah dihapus atau tidak diklaim — rawan diambil alih oleh penyerang.', italic=True)
        rows = [
            [t.get('id', '-'), t.get('subdomain', '-'), t.get('cname', '-'),
             t.get('service', '-'),
             'CONFIRMED' if t.get('confirmed') else 'KANDIDAT',
             t.get('severity', 'HIGH')]
            for t in items
        ]
        self.table(
            ['ID', 'Subdomain', 'CNAME Target', 'Layanan', 'Status', 'Severity'],
            rows, widths=[0.7, 1.9, 1.9, 1.1, 1.0, 0.8], severity_col=5
        )
        for t in items:
            if t.get('note'):
                self.bullet(f"{t.get('id','')}: {t['note']}")

    def oauth_analysis(self):
        items = self.triage.get('oauth_analysis', [])
        if not items:
            self.P('Tidak ada OAuth 2.0 / OIDC flow yang terdeteksi atau tidak ada kerentanan yang ditemukan.', italic=True)
            return
        self.P('OAuth 2.0 dan OIDC flow diuji untuk redirect_uri bypass, state CSRF, implicit token leak, PKCE bypass, dan account linking abuse.', italic=True)
        for o in items:
            sev = str(o.get('severity', 'HIGH')).upper()
            h = self.H(f"{o.get('id', '-')} — {o.get('flow', '-')}", 2)
            for r in h.runs:
                if sev in SEV_RGB: r.font.color.rgb = SEV_RGB[sev]
            meta = [
                ['Flow / Grant Type', o.get('flow', '-')],
                ['Kerentanan', o.get('vulnerability', '-')],
                ['Severity', sev],
                ['Eksploit Berhasil', o.get('exploit', '-')],
            ]
            self.table(['Parameter', 'Nilai'], meta, widths=[1.8, 4.8])

    def twofa_analysis(self):
        items = self.triage.get('twofa_analysis', [])
        if not items:
            self.P('Tidak ada 2FA/OTP yang terdeteksi atau tidak ada bypass yang berhasil.', italic=True)
            return
        self.P('Mekanisme 2FA dan OTP diuji: rate limit, code reuse, skip step, response manipulation, dan brute-force.', italic=True)
        rows = [
            [t.get('id', '-'), t.get('method', '-'), t.get('vulnerability', '-')[:70],
             t.get('severity', 'HIGH')]
            for t in items
        ]
        self.table(['ID', 'Metode 2FA', 'Kerentanan', 'Severity'], rows,
                   widths=[0.7, 1.2, 4.1, 0.8], severity_col=3)
        for t in items:
            if t.get('exploit'):
                self.bullet(f"{t.get('id','')}: {t['exploit']}")

    def api_versions(self):
        items = self.triage.get('api_versions', [])
        if not items:
            self.P('Tidak ada endpoint API versi lama yang teridentifikasi.', italic=True)
            return
        self.P('Endpoint API versi lama (deprecated) sering memiliki kontrol akses yang lebih lemah dibanding versi terkini.', italic=True)
        rows = [
            [a.get('id', '-'), a.get('endpoint', '-'), a.get('current', '-'),
             a.get('finding', '-')[:60], a.get('severity', 'MEDIUM')]
            for a in items
        ]
        self.table(['ID', 'Endpoint Lama', 'Versi Current', 'Temuan', 'Severity'],
                   rows, widths=[0.7, 1.7, 1.0, 3.0, 0.9], severity_col=4)

    def blind_findings(self):
        items = self.triage.get('blind_findings', [])
        if not items:
            self.P('Tidak ada blind vulnerability (OOB/canary) yang terkonfirmasi.', italic=True)
            return
        self.P('Kerentanan yang dideteksi via Out-of-Band callback (DNS canary, canary domain) — tidak langsung terlihat dari response HTTP biasa.', italic=True)
        rows = [
            [b.get('id', '-'), b.get('type', '-'), b.get('location', '-')[:50],
             b.get('canary_hit', '-')[:60], b.get('severity', 'HIGH')]
            for b in items
        ]
        self.table(['ID', 'Tipe', 'Lokasi / Parameter', 'Canary Callback', 'Severity'],
                   rows, widths=[0.7, 1.2, 2.0, 2.5, 0.9], severity_col=4)

    def business_logic(self):
        items = self.triage.get('business_logic', [])
        if not items:
            self.P('Tidak ada business logic flaw yang teridentifikasi.', italic=True)
            return
        self.P('Pengujian logika bisnis: negative price, coupon stacking, race condition pada limit, privilege escalation, workflow skip, dan role boundary bypass.', italic=True)
        rows = [
            [b.get('id', '-'), b.get('type', '-'), b.get('location', '-')[:45],
             b.get('finding', '-')[:65], b.get('severity', 'HIGH')]
            for b in items
        ]
        self.table(['ID', 'Tipe', 'Lokasi', 'Temuan', 'Severity'],
                   rows, widths=[0.7, 1.4, 1.6, 2.7, 0.9], severity_col=4)

    def cache_poisoning(self):
        items = self.triage.get('cache_poisoning', [])
        if not items:
            self.P('Tidak ada cache poisoning atau cache deception yang terkonfirmasi.', italic=True)
            return
        self.P('Web Cache Poisoning via unkeyed header injection dan Web Cache Deception via path confusion diuji pada semua endpoint publik.', italic=True)
        rows = [
            [c.get('id', '-'), c.get('type', '-'),
             c.get('header', c.get('path', '-'))[:45],
             'CONFIRMED' if c.get('confirmed') else 'PARTIAL',
             c.get('severity', 'HIGH')]
            for c in items
        ]
        self.table(['ID', 'Tipe', 'Vector', 'Konfirmasi', 'Severity'],
                   rows, widths=[0.7, 1.6, 2.5, 1.0, 0.9], severity_col=4)

    def smuggling(self):
        items = self.triage.get('smuggling', [])
        if not items:
            self.P('Tidak ada HTTP Request Smuggling (CL.TE / TE.CL / HTTP/2 downgrade) yang terkonfirmasi.', italic=True)
            return
        self.P('HTTP Request Smuggling diuji via desync antara Content-Length dan Transfer-Encoding header. Teknik: CL.TE, TE.CL, TE.TE obfuscation, dan HTTP/2 downgrade ke HTTP/1.', italic=True)
        rows = [
            [s.get('id', '-'), s.get('variant', '-'), s.get('endpoint', '-')[:45],
             s.get('finding', '-')[:65], s.get('severity', 'CRITICAL')]
            for s in items
        ]
        self.table(['ID', 'Variant', 'Endpoint', 'Temuan', 'Severity'],
                   rows, widths=[0.7, 1.0, 1.8, 3.1, 0.9], severity_col=4)
        for s in items:
            if s.get('poc_snippet'):
                self.H('PoC Request', 3)
                self.P(s['poc_snippet'], mono=True if hasattr(self, '_mono') else False)

    def injection_advanced(self):
        items = self.triage.get('injection_advanced', [])
        if not items:
            self.P('Tidak ada SSTI, XXE, Prototype Pollution, LFI, atau Clickjacking yang terkonfirmasi.', italic=True)
            return
        self.P('Pengujian injeksi lanjutan mencakup SSTI (Jinja2/Twig/ERB/Freemarker), XXE via upload XML/SVG/DOCX, Prototype Pollution via JSON __proto__, LFI via path traversal, dan Clickjacking via X-Frame-Options absent.', italic=True)
        rows = [
            [i.get('id', '-'), i.get('type', '-'), i.get('location', '-')[:40],
             i.get('payload', '-')[:40], i.get('finding', '-')[:45],
             i.get('severity', 'HIGH')]
            for i in items
        ]
        self.table(['ID', 'Tipe', 'Lokasi', 'Payload', 'Hasil', 'Severity'],
                   rows, widths=[0.7, 1.1, 1.5, 1.5, 1.8, 0.8], severity_col=5)

    def client_side(self):
        items = self.triage.get('client_side', [])
        if not items:
            self.P('Tidak ada CORS wildcard credentialed atau DNS Rebinding yang terkonfirmasi.', italic=True)
            return
        self.P('Pengujian client-side mencakup CORS credentialed wildcard (bukti fetch aktual), dan DNS Rebinding via TTL manipulation untuk bypass same-origin policy.', italic=True)
        rows = [
            [c.get('id', '-'), c.get('type', '-'), c.get('origin_tested', '-')[:40],
             c.get('finding', '-')[:60], c.get('severity', 'HIGH')]
            for c in items
        ]
        self.table(['ID', 'Tipe', 'Origin Diuji', 'Temuan', 'Severity'],
                   rows, widths=[0.7, 1.3, 1.9, 2.7, 0.9], severity_col=4)

    def supply_chain(self):
        items = self.triage.get('supply_chain', [])
        if not items:
            self.P('Tidak ada dependency confusion atau supply chain attack vector yang teridentifikasi.', italic=True)
            return
        self.P('Dependency Confusion diuji: nama package internal yang ditemukan di JS/config file dicek apakah tersedia di registry publik (npm, PyPI, RubyGems). Package publik dengan nama sama bisa di-install oleh build pipeline target.', italic=True)
        rows = [
            [s.get('id', '-'), s.get('package', '-'), s.get('registry', '-'),
             'ADA di publik' if s.get('public_exists') else 'TIDAK ada di publik',
             s.get('found_in', '-')[:45], s.get('severity', 'HIGH')]
            for s in items
        ]
        self.table(['ID', 'Package', 'Registry', 'Status Publik', 'Ditemukan Di', 'Severity'],
                   rows, widths=[0.6, 1.5, 0.8, 1.2, 2.1, 0.8], severity_col=5)

    def mobile_deeplink(self):
        items = self.triage.get('mobile_deeplink', [])
        if not items:
            self.P('Tidak ada mobile deep link hijacking atau intent abuse yang teridentifikasi.', italic=True)
            return
        self.P('Deep link dan intent scheme diuji: exported activity tanpa permission guard, universal link yang bisa di-intercept, dan scheme handler yang tidak memvalidasi origin.', italic=True)
        rows = [
            [m.get('id', '-'), m.get('type', '-'), m.get('scheme', '-')[:35],
             m.get('component', '-')[:35], m.get('finding', '-')[:50],
             m.get('severity', 'HIGH')]
            for m in items
        ]
        self.table(['ID', 'Tipe', 'Scheme / Link', 'Component', 'Temuan', 'Severity'],
                   rows, widths=[0.6, 1.0, 1.5, 1.4, 2.1, 0.8], severity_col=5)

    def recon(self):
        r = self.triage.get('recon', {})
        self.P('Hasil pemetaan permukaan serangan (attack surface), subdomain, endpoint publik, teknologi, dan secret yang teridentifikasi.', italic=True)

        # Subdomain enumeration results
        subdomains = r.get('subdomains_found', [])
        if subdomains:
            self.H('Subdomain Teridentifikasi', 2)
            rows = [[s if isinstance(s, str) else s.get('host', '-'),
                     s.get('ip', '-') if isinstance(s, dict) else '-',
                     s.get('status', '-') if isinstance(s, dict) else '-',
                     s.get('tech', '-') if isinstance(s, dict) else '-']
                    for s in subdomains]
            self.table(['Subdomain', 'IP', 'HTTP Status', 'Teknologi'], rows, widths=[2.4, 1.3, 0.9, 2.0])

        # Technology fingerprint
        tech = r.get('tech_stack', [])
        if tech:
            self.H('Fingerprint Teknologi & Stack', 2)
            self.P('Terdeteksi: ' + ', '.join(tech if isinstance(tech, list) else [str(tech)]))

        # Endpoint map
        endpoints = r.get('endpoints', [])
        if endpoints:
            self.H('Peta Endpoint Teridentifikasi', 2)
            rows = [[ep.get('method','GET'), ep.get('url','-'), ep.get('auth','Public'), str(ep.get('status','-'))]
                    for ep in endpoints]
            self.table(['Method', 'URL / Path', 'Auth Required', 'Status Code'], rows, widths=[0.9, 3.8, 1.1, 0.8])

        # Hardcoded secrets
        secrets = r.get('secrets_detected', [])
        if secrets:
            self.H('Credential & Secret Hardcoded Terdeteksi', 2)
            rows = [[s.get('type','Secret'), s.get('location','-'), s.get('value','(...)'), s.get('risk','MEDIUM')]
                    for s in secrets]
            self.table(['Jenis Secret', 'Lokasi / File', 'Nilai Terdeteksi', 'Risiko'], rows,
                       widths=[1.3, 2.4, 2.1, 0.8], severity_col=3)

        self.blocks(self.cfg.get('recon_blocks', []))

    def kill_chains(self):
        chains = self.triage.get('kill_chains', [])
        if not chains:
            self.P('Tidak ada exploit chain yang berhasil dieksekusi pada sesi ini.', italic=True)
            return
        self.P('Rangkaian eksploitasi (kill chain) yang berhasil dibuktikan. Tiap chain menggabungkan dua atau lebih kerentanan menjadi satu jalur serangan dengan dampak akhir yang terukur.', italic=True)
        for kc in chains:
            sev = str(kc.get('severity', 'HIGH')).upper()
            h = self.H(f"{kc.get('id','-')} — {kc.get('name','-')}", 2)
            for r in h.runs:
                if sev in SEV_RGB: r.font.color.rgb = SEV_RGB[sev]

            meta_rows = [
                ['Severity / CVSS', f"{sev} — {kc.get('cvss','(-)')}"],
                ['Status Verifikasi', kc.get('status', 'VERIFIED')],
                ['Dampak Akhir', kc.get('business_impact', '-')],
            ]
            self.table(['Parameter', 'Nilai'], meta_rows, widths=[1.8, 4.8])

            steps = kc.get('steps', [])
            if steps:
                self.P('Urutan Eksploitasi:', bold=True)
                for i, s in enumerate(steps, 1):
                    self.bullet(f"[{i}] {s}")

            shots = kc.get('evidence', [])
            for shot in shots:
                ref = os.path.basename(shot) if isinstance(shot, str) else shot
                fp = self.resolve_image(ref)
                if fp:
                    self.image(ref, f"Bukti: {kc.get('id','-')} — {os.path.basename(fp)}")
                    break

    def findings(self):
        self.P('Temuan kerentanan diurutkan berdasarkan tingkat keparahan. Setiap temuan dilengkapi langkah pembuktian konsep (Proof of Concept) yang dapat direproduksi.', italic=True)
        used = set()
        for f in self._findings:
            h = self.H(f"{f['id']} — {f['title']}", 2)
            for r in h.runs:
                if f['severity'] in SEV_RGB: r.font.color.rgb = SEV_RGB[f['severity']]
            
            meta_rows = [
                ['Severity', f['severity']],
                ['Kategori / CWE', f"{f['category']} ({f['cwe']})"],
                ['Status', f['status']],
                ['Skor Risiko (L × I)', f"{f['score']} (Likelihood: {f['likelihood']}, Impact: {f['impact_score']})"],
            ]
            if f['cvss'] != '-': meta_rows.append(['CVSS v3.1', str(f['cvss'])])
            if f['location']: meta_rows.append(['Lokasi / Endpoint', str(f['location'])])
            self.table(['Parameter', 'Nilai'], meta_rows, widths=[1.8, 4.8])

            if f['steps']:
                self.P('Langkah Reproduksi (Proof of Concept):', bold=True)
                for s in f['steps']: self.bullet(s)

            if f.get('poc_snippet'):
                self.P('Snippet Request / Response / Payload:', bold=True)
                self.P(str(f['poc_snippet']), italic=True)

            self.P('Ekspektasi: ' + str(f['expected']))
            self.P('Aktual: ' + str(f['actual']))
            if f['business']: self.P('Dampak Bisnis & Keamanan: ' + str(f['business']))
            self.P('Rekomendasi Remediasi: ' + str(f['recommendation']))
            if f['evidence']:
                self.P('Bukti: ' + '; '.join(map(str, f['evidence'])) +
                       (f" (keyakinan: {f['confidence']})" if f['confidence'] != '-' else ''), italic=True)
            if not any(s.get('highlight') for s in f['shots']):
                self.P('CATATAN: screenshot PoC temuan ini belum diberi lingkaran merah di triage.json.',
                       italic=True)
            for shot in f['shots']:
                ref = shot.get('ref', '') if isinstance(shot, dict) else str(shot)
                fp = self.resolve_image(ref)
                if fp and fp not in used:
                    self.image(ref,
                               f"Bukti Visual: {f['id']} — {os.path.basename(fp)}",
                               highlight=shot.get('highlight') if isinstance(shot, dict) else None,
                               label=shot.get('label', '') if isinstance(shot, dict) else '')
                    used.add(fp)

    def chaos(self):
        ch = self.triage.get('chaos', {})
        self.P('Hasil pengujian chaos / monkey testing untuk memverifikasi resiliensi aplikasi terhadap input ekstrem, kondisi balapan (race condition), serta verifikasi bahwa seluruh jejak pengujian telah dibersihkan.', italic=True)
        
        # Cleanup status banner
        cl_status = str(ch.get('cleanup_status', 'VERIFIED')).upper()
        if 'PARTIAL' in cl_status or 'FAILED' in cl_status:
            self.banner(f"STATUS CLEANUP: {cl_status} — PERLU PEMBERSIHAN MANUAL OLEH VENDOR", fill='B00000', size=11)
        else:
            self.banner(f"STATUS CLEANUP PASCA-UJI: TERVERIFIKASI BERSIH (VERIFIED)", fill='336633', size=11)

        tests = ch.get('tests', [])
        if tests:
            self.H('Skenario Chaos & Monkey Testing', 2)
            rows = [[t.get('scenario','Chaos'), t.get('target','-'), t.get('response','Graceful'), t.get('finding_ref','-')]
                    for t in tests]
            self.table(['Skenario Pengujian', 'Komponen / Endpoint Target', 'Respon Sistem', 'Temuan Terkait'], rows,
                       widths=[2.0, 2.2, 1.6, 0.8])

        cleanup_items = ch.get('cleanup_items', [])
        if cleanup_items:
            self.H('Inventaris Pembersihan Jejak (Teardown)', 2)
            rows = [[ci.get('item','Artefak'), ci.get('method','-'), ci.get('status','BERSIH'), ci.get('notes','-')]
                    for ci in cleanup_items]
            self.table(['Jejak / Artefak', 'Metode Pembersihan', 'Status', 'Catatan'], rows,
                       widths=[1.8, 1.8, 1.1, 1.9])
        self.blocks(self.cfg.get('chaos_blocks', []))

    def passed(self):
        self.P('Pemeriksaan keamanan dan fungsional yang dinyatakan lolos tanpa kerentanan.', italic=True)
        for c in self.triage.get('passed_checks', []): self.bullet(c)

    def risk(self):
        self.P('Skor Risiko = Likelihood × Impact (1–5). Band: 20–25 Critical, 12–19 High, 6–11 Medium, 1–5 Low.', italic=True)
        rows = [[f['id'], f['title'][:50], str(f['likelihood']), str(f['impact_score']),
                 str(f['score']), f.get('owner','tidak ditetapkan'), str(f['recommendation'])[:88], f['status']]
                for f in self._findings]
        self.table(['ID', 'Kerentanan', 'L', 'I', 'Skor', 'Owner', 'Rencana Mitigasi', 'Status'], rows,
                   widths=[0.65, 1.75, 0.3, 0.3, 0.45, 0.65, 2.0, 0.8], score_col=4)

    def recommendations(self):
        groups = [('P1 — Tindakan Segera (CRITICAL & HIGH)', ('CRITICAL','HIGH')),
                  ('P2 — Tindakan Terjadwal (MEDIUM)', ('MEDIUM',)),
                  ('P3 — Peningkatan Keamanan Lanjutan (LOW & INFO)', ('LOW','INFO'))]
        for title, sevs in groups:
            items = [f"{f['id']}: {f['recommendation']}" for f in self._findings if f['severity'] in sevs]
            if not items: continue
            self.H(title, 2)
            for it in items: self.bullet(it)

    def db_verification(self):
        """Render hasil db_verify.py dari pendukung/ai/db-verification.json."""
        path = os.path.join(self.base, 'ai', 'db-verification.json')
        if not os.path.isfile(path):
            self.P('Tidak ada hasil verifikasi database. Tambahkan `db_verification` ke '
                   '`report.chapters` dan jalankan `db_verify.py` bila pembuktian berbasis data diperlukan.',
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
        self.P('Koneksi bersifat read-only dan hanya berlaku pada scope berotorisasi. '
               'Kredensial tidak pernah ditulis ke dokumen ini.', italic=True)

    def limits(self):
        self.P('Batasan pengujian, scope yang tidak diuji, dan dependensi lingkungan.', italic=True)
        for x in self.triage.get('limitations', []): self.bullet(x)
        if self.cfg.get('limit_note'): self.P(self.cfg['limit_note'], bold=True)
        self.blocks(self.cfg.get('limits_blocks', []))

    def conclusion(self):
        tr = self.triage
        s = tr.get('summary', {}) or {}
        by = s.get('by_severity', {}) or {}
        crit = int(by.get('CRITICAL', 0) or 0)
        high = int(by.get('HIGH', 0) or 0)
        med = int(by.get('MEDIUM', 0) or 0)
        low = int(by.get('LOW', 0) or 0)
        info = int(by.get('INFO', 0) or 0)
        total = int(s.get('total_findings', len(self._findings)) or 0)
        if crit:
            status = 'KRITIS — TIDAK LOLOS, perbaikan segera sebelum rilis'
        elif high:
            status = 'RISIKO TINGGI — perbaikan wajib sebelum rilis'
        elif med:
            status = 'RISIKO SEDANG — perbaikan dijadwalkan'
        elif total:
            status = 'RISIKO RENDAH — perbaikan lanjutan'
        else:
            status = 'TIDAK ADA KERENTANAN TERKONFIRMASI'

        self.P('Kesimpulan akhir dari seluruh fase pengujian, merangkum status risiko, temuan utama, dan keputusan lanjutan.', italic=True)
        rows = [
            ['Status akhir', status],
            ['Total temuan', str(total)],
            ['Distribusi', f'CRITICAL {crit} | HIGH {high} | MEDIUM {med} | LOW {low} | INFO {info}'],
            ['Verdict', str(tr.get('verdict') or s.get('verdict') or '-')],
            ['Lingkungan', str(tr.get('environment', '-'))],
            ['Status cleanup', str((tr.get('chaos') or {}).get('cleanup_status', '-'))],
        ]
        self.table(['Aspek', 'Nilai'], rows, widths=[1.6, 5.0])

        self.H('Simpulan Utama', 2)
        if total:
            top = self._findings[0]
            self.bullet(f"Temuan paling signifikan: {top['id']} — {top['title']} ({top['severity']}).")
            self.bullet(f"Sebanyak {total} temuan terkonfirmasi; prioritas penanganan mengikuti urutan severity pada bab Risk Register dan Rekomendasi.")
        else:
            self.bullet('Tidak ada kerentanan yang terkonfirmasi pada cakupan dan metode yang dijalankan.')
        passed = tr.get('passed_checks', []) or []
        if passed:
            self.bullet(f"Sebanyak {len(passed)} pemeriksaan dinyatakan lolos dan menjadi bukti bahwa kontrol existing berfungsi.")
        chains = tr.get('kill_chains', []) or []
        self.bullet(f"Exploit chain yang berhasil: {len(chains)}. " +
                    ("Tidak ada rangkaian eksploitasi yang meningkatkan dampak temuan."
                     if not chains else "Temuan terkait deverifikasi dengan chain tersebut dan severity disesuaikan."))
        self.bullet('Hasil pengujian ini gambaran pada titik waktu pelaksanaan; konfigurasi atau kode baru dapat mengubah status risiko.')

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
        self.blocks(self.cfg.get('conclusion_blocks', []))

    def appendix_cases(self):
        path = os.path.join(self.base, 'ai', 'generated-cases.md')
        if not os.path.isfile(path):
            self.P('[Berkas generated-cases.md tidak tersedia]', italic=True); return
        lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1; continue
            if line.startswith('#'):
                lvl = min(len(line) - len(line.lstrip('#')), 3)
                self.H(line.lstrip('#').strip(), max(lvl, 2))
                i += 1; continue
            if line.startswith('|') and i + 1 < len(lines) and '|---' in lines[i+1]:
                headers = [c.strip() for c in line.split('|')[1:-1]]
                i += 2; rows = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    rows.append([c.strip() for c in lines[i].strip().split('|')[1:-1]])
                    i += 1
                widths = [0.8, 1.4, 2.4, 0.9, 1.1] if len(headers) == 5 else None
                status_col = 3 if len(headers) == 5 else None
                self.table(headers, rows, widths=widths, severity_col=status_col)
                continue
            if line.startswith(('-', '*')):
                self.bullet(line.lstrip('-*').strip())
            else:
                self.P(line)
            i += 1

    def appendix_submissions(self):
        findings = self._findings
        if not findings:
            self.P('Tidak ada temuan untuk dibuatkan draft submission.', italic=True)
            return
        self.P('Format draft submission siap pakai untuk pelaporan bug bounty (HackerOne, Bugcrowd, dan format umum) yang digabungkan langsung di dokumen ini.', italic=True)
        vrt_map = {'CRITICAL': 'P1', 'HIGH': 'P2', 'MEDIUM': 'P3', 'LOW': 'P4', 'INFO': 'P5'}
        for f in findings[:5]:
            sev = str(f.get('severity', 'HIGH')).upper()
            h = self.H(f"{f['id']} — {f['title']}", 2)
            for r in h.runs:
                if sev in SEV_RGB: r.font.color.rgb = SEV_RGB[sev]

            # HackerOne Draft Format
            self.H('Format HackerOne', 3)
            ho_meta = [
                ['Title / Summary', f['title']],
                ['Severity', f"{sev} (CVSS: {f.get('cvss', f['score'])})"],
                ['Weakness / CWE', f.get('cwe', '-')],
                ['Impact', f['business']],
                ['Remediation', f['recommendation']],
            ]
            self.table(['Field', 'Content'], ho_meta, widths=[1.8, 4.8])
            if f.get('steps'):
                self.P('Steps to Reproduce:', bold=True)
                for i, s in enumerate(f['steps'], 1):
                    self.bullet(f"{i}. {s}")
            if f.get('poc_snippet'):
                self.P('PoC / HTTP Request:', bold=True)
                self.P(f['poc_snippet'])

            # Bugcrowd Draft Format
            self.H('Format Bugcrowd', 3)
            bc_meta = [
                ['Title', f['title']],
                ['VRT Priority', vrt_map.get(sev, 'P3')],
                ['CVSS Score', str(f.get('cvss', f['score']))],
                ['CWE', f.get('cwe', '-')],
                ['Remediation', f['recommendation']],
            ]
            self.table(['Field', 'Value'], bc_meta, widths=[1.8, 4.8])

    def appendix_evidence(self):
        self.P('Daftar berkas artefak, capture traffic, dan screenshot yang tersimpan di direktori pendukung/bukti.', italic=True)
        bukti_dir = os.path.join(self.base, 'bukti')
        shots_dir = os.path.join(self.base, 'screenshots')
        rows = []
        for d, label in [(bukti_dir, 'Bukti / Capture'), (shots_dir, 'Screenshot')]:
            if not os.path.isdir(d): continue
            for root, _, files in os.walk(d):
                for f in sorted(files):
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, self.base)
                    sz = os.path.getsize(fp)
                    rows.append([rel.replace('\\','/'), label, f"{sz:,} B", sha256(fp)[:16] + '...'])
        if rows:
            self.table(['Path Berkas', 'Kategori', 'Ukuran', 'SHA-256 (Prefix)'], rows[:60],
                       widths=[2.8, 1.3, 1.0, 1.5])
        else:
            self.P('Tidak ada berkas bukti di pendukung/bukti/.', italic=True)

    def appendix_extra(self):
        shots = self.cfg.get('extra_shots', [])
        if not shots:
            self.P('Tidak ada gambar bukti visual tambahan yang didefinisikan di profil laporan.', italic=True); return
        self.P('Berikut bukti visual dari sesi pengujian. Semua gambar tertanam di dokumen ini.')
        for item in shots:
            ref, cap = item if isinstance(item, (list, tuple)) else (item, str(item))
            self.image(ref, cap)

    # ---------- data-driven extra blocks ----------
    def blocks(self, blocks):
        for b in blocks:
            typ = b.get('type', 'paragraph')
            if typ == 'table':
                self.table(b.get('headers',[]), b.get('rows',[]), b.get('widths'),
                           score_col=b.get('score_col'), severity_col=b.get('severity_col'))
            elif typ == 'heading':
                self.H(b.get('text',''), b.get('level', 2))
            elif typ == 'bullets':
                for it in b.get('items', []): self.bullet(it)
            elif typ == 'flow_table':
                self._flow_table(b)
            else:
                self.P(b.get('text',''), bold=b.get('bold',False), italic=b.get('italic',False))

    def _flow_table(self, b):
        flows_path = os.path.join(self.base, 'bukti', 'network', 'flows.jsonl')
        if not os.path.isfile(flows_path):
            self.P('[Traffic capture flows.jsonl tidak tersedia]', italic=True); return
        rows = []
        param_subs = self.cfg.get('flow_param_values', {})
        for line in open(flows_path, encoding='utf-8', errors='replace'):
            if not line.strip(): continue
            try:
                fl = json.loads(line)
            except Exception:
                continue
            u = fl.get('url','-')
            for placeholder, actual_val in param_subs.items():
                if placeholder in u:
                    u = u.replace(placeholder, str(actual_val))
            rows.append([fl.get('method','-'), u[:120], str(fl.get('status','-')),
                         f"{fl.get('duration_ms',0):.1f}" if isinstance(fl.get('duration_ms'), (int,float)) else '-',
                         str(fl.get('response_size',0))])
        if rows:
            self.table(['Method','URL','Status','Lat (ms)','Size (B)'], rows, widths=[0.7, 4.0, 0.6, 0.7, 0.7])


def infer_profile(triage):
    p = triage.get('report', {}).get('profile')
    if p: return p
    mode = str(triage.get('mode', '')).lower()
    if 'apk' in mode or 'mobile' in mode: return 'apk'
    if 'web' in mode: return 'web'
    return 'bughunt'


def build(root, profile_override=None, output_override=None):
    root = os.path.abspath(root)
    triage = json.load(open(os.path.join(root,'pendukung','ai','triage.json'), encoding='utf-8'))
    cfg = triage.get('report', {})
    profile = profile_override or cfg.get('profile') or infer_profile(triage)
    chapters = cfg.get('chapters') or DEFAULT_CHAPTERS.get(profile, DEFAULT_CHAPTERS['bughunt'])
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
            if hasattr(rep, ch):
                getattr(rep, ch)()
        else:
            rep.H(f"{n}. {ch.get('title','Bagian')}", 1)
            rep.blocks(ch.get('blocks', []))
    out = output_override or os.path.join(root, cfg.get('output', f'Laporan-BugHunter-{profile}-{triage.get("date", "assessment")}.docx'))
    rep.doc.save(out)
    print('SAVED', out)
    print('PROFILE', profile, 'CHAPTERS', len([c for c in chapters if c != 'cover']),
          'FINDINGS', len(rep._findings), 'KILL CHAINS', len(triage.get('kill_chains',[])),
          'TABLES', len(rep.doc.tables), 'IMAGES', len(rep.doc.inline_shapes))

    # Generate watch dashboard (static, updated each run)
    _gen_dashboard(root, triage)
    return out


def _gen_dashboard(root, triage):
    """Generate watch-dashboard.html + compute watch diff vs triage-prev.json."""
    import datetime, shutil
    target = triage.get('target', 'Target')
    date = triage.get('date', str(datetime.date.today()))
    verdict = triage.get('verdict', triage.get('summary', {}).get('verdict', 'PENDING'))
    findings = norm_findings(triage)
    chains = triage.get('kill_chains', [])
    summary = triage.get('summary', {})
    by_sev = summary.get('by_severity', {})
    jwts = triage.get('jwt_analysis', [])
    cves = triage.get('cve_matches', [])
    waf = triage.get('waf', {})
    oauths = triage.get('oauth_analysis', [])
    twofas = triage.get('twofa_analysis', [])
    blinds = triage.get('blind_findings', [])
    bizlogics = triage.get('business_logic', [])
    caches = triage.get('cache_poisoning', [])
    takeovers = triage.get('subdomain_takeover', [])
    smugglings = triage.get('smuggling', [])
    injections = triage.get('injection_advanced', [])
    client_sides = triage.get('client_side', [])
    supply_chains = triage.get('supply_chain', [])
    deeplinks = triage.get('mobile_deeplink', [])

    # Watch diff — compare with previous triage
    ai_dir = os.path.join(root, 'pendukung', 'ai')
    prev_path = os.path.join(ai_dir, 'triage-prev.json')
    new_ids = set(f['id'] for f in findings)
    prev_ids = set()
    changed_sev = {}
    if os.path.isfile(prev_path):
        try:
            prev = json.load(open(prev_path, encoding='utf-8'))
            prev_findings = norm_findings(prev)
            prev_ids = set(f['id'] for f in prev_findings)
            prev_sev = {f['id']: f['severity'] for f in prev_findings}
            for f in findings:
                if f['id'] in prev_sev and prev_sev[f['id']] != f['severity']:
                    changed_sev[f['id']] = f"{'↑' if SEV_LI.get(f['severity'],(0,))[0] > SEV_LI.get(prev_sev[f['id']],(0,))[0] else '↓'} {prev_sev[f['id']]} → {f['severity']}"
        except Exception:
            pass
    # Save current as prev for next run
    curr_path = os.path.join(ai_dir, 'triage.json')
    if os.path.isfile(curr_path) and os.path.isdir(ai_dir):
        try: shutil.copy2(curr_path, prev_path)
        except Exception: pass

    added_ids = new_ids - prev_ids
    removed_ids = prev_ids - new_ids

    sev_color = {'CRITICAL': '#B00000', 'HIGH': '#C05000', 'MEDIUM': '#8A6D00',
                 'LOW': '#336633', 'INFO': '#2B5B84', 'OPEN': '#8A6D00',
                 'VERIFIED': '#336633', 'PARTIAL': '#B00000'}

    def badge(text, color=None):
        c = color or sev_color.get(str(text).upper(), '#555')
        return f'<span style="background:{c};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:bold">{text}</span>'

    def finding_row(f):
        is_new = f['id'] in added_ids
        is_changed = f['id'] in changed_sev
        highlight = ' style="background:#2A3A00"' if is_new else (' style="background:#2A1A00"' if is_changed else '')
        new_tag = ' 🆕' if is_new else ''
        chg_tag = f' ({changed_sev[f["id"]]})' if is_changed else ''
        return (f'<tr{highlight}><td>{f["id"]}{new_tag}</td><td>{f["title"][:55]}{chg_tag}</td>'
                f'<td>{badge(f["severity"])}</td>'
                f'<td style="text-align:center;font-weight:bold">{f["score"]}</td>'
                f'<td>{f["status"]}</td></tr>')

    finding_rows = ''.join(finding_row(f) for f in sorted(findings, key=lambda x: x['score'], reverse=True))

    chain_rows = ''.join(
        f'<tr><td>{kc.get("id","-")}</td><td>{kc.get("name","-")[:55]}</td>'
        f'<td>{badge(kc.get("severity","HIGH"))}</td>'
        f'<td>{badge(kc.get("status","VERIFIED"), sev_color.get(str(kc.get("status","VERIFIED")).upper(),"#555"))}</td></tr>'
        for kc in chains
    )

    jwt_rows = ''.join(
        f'<tr><td>{j.get("id","-")}</td><td>{j.get("algorithm","-")}</td>'
        f'<td>{badge(j.get("severity","HIGH"))}</td>'
        f'<td>{j.get("vulnerability","-")[:60]}</td></tr>'
        for j in jwts
    )

    cve_rows = ''.join(
        f'<tr><td>{c.get("component","-")}</td><td>{c.get("cve","-")}</td>'
        f'<td style="font-weight:bold;color:{"#B00000" if float(str(c.get("cvss",0)).split()[0] if str(c.get("cvss",0)).replace(".","").isdigit() else 0)>=9 else "#C05000"}">{c.get("cvss","-")}</td>'
        f'<td>{"🔴 RENTAN" if c.get("likely_vulnerable") else "⚠️ Verifikasi"}</td></tr>'
        for c in cves
    )

    waf_badge = badge(f"WAF: {waf.get('type','Tidak Terdeteksi')}", '#1B365D' if waf.get('detected') else '#336633')
    cleanup_status = triage.get('chaos', {}).get('cleanup_status', 'VERIFIED')
    cleanup_badge = badge(f'CLEANUP: {cleanup_status}', sev_color.get(cleanup_status.upper(), '#555'))

    diff_summary = ''
    if added_ids or removed_ids or changed_sev:
        diff_summary = f'''<div class="section">
  <h2>⚡ Diff vs Sesi Sebelumnya</h2>
  <table><thead><tr><th>Perubahan</th><th>ID</th></tr></thead><tbody>
  {''.join(f'<tr style="background:#2A3A00"><td>🆕 Temuan Baru</td><td>{i}</td></tr>' for i in sorted(added_ids))}
  {''.join(f'<tr style="background:#1A2A1A"><td>✅ Hilang / Resolved</td><td>{i}</td></tr>' for i in sorted(removed_ids))}
  {''.join(f'<tr style="background:#2A1A00"><td>⚠️ Severity Berubah</td><td>{i}: {v}</td></tr>' for i, v in sorted(changed_sev.items()))}
  </tbody></table></div>'''

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="10">
<title>Bug Hunter — Live Dashboard — {target}</title>
<style>
  body {{font-family:Calibri,Arial,sans-serif;margin:0;background:#0E1A2B;color:#E8EDF5}}
  header {{background:#1B2F4A;padding:16px 28px;border-bottom:3px solid #2E6DA4}}
  h1 {{margin:0;font-size:20px;color:#7EC8E3}} h2 {{color:#A8C8E8;font-size:15px;margin:14px 0 6px}}
  .meta {{font-size:12px;color:#8A9BAD;margin-top:4px}}
  .grid {{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;padding:18px 28px}}
  .card {{background:#1B2F4A;border-radius:8px;padding:14px;text-align:center}}
  .card .num {{font-size:30px;font-weight:bold}} .card .lbl {{font-size:12px;color:#8A9BAD}}
  .section {{padding:0 28px 20px}} table {{width:100%;border-collapse:collapse;font-size:13px}}
  th {{background:#1B2F4A;padding:8px 10px;text-align:left;color:#7EC8E3}}
  td {{padding:7px 10px;border-bottom:1px solid #152030}}
  tr:nth-child(even) td {{background:rgba(255,255,255,0.03)}}
  .verdict {{padding:14px 28px;font-size:16px;font-weight:bold}}
  .footer {{padding:10px 28px;font-size:11px;color:#8A9BAD;border-top:1px solid #1B2F4A;margin-top:10px}}
  span {{display:inline-block}}
</style>
</head>
<body>
<header>
  <h1>🎯 Bug Hunter — Live Dashboard</h1>
  <div class="meta">Target: <b style="color:#7EC8E3">{target}</b> &nbsp;|&nbsp; {date} &nbsp;|&nbsp; Auto-refresh: 10s &nbsp;|&nbsp; {waf_badge}</div>
</header>

<div class="grid">
  <div class="card"><div class="num" style="color:#B00000">{by_sev.get('CRITICAL',0)}</div><div class="lbl">CRITICAL</div></div>
  <div class="card"><div class="num" style="color:#C05000">{by_sev.get('HIGH',0)}</div><div class="lbl">HIGH</div></div>
  <div class="card"><div class="num" style="color:#8A6D00">{by_sev.get('MEDIUM',0)}</div><div class="lbl">MEDIUM</div></div>
  <div class="card"><div class="num" style="color:#336633">{by_sev.get('LOW',0)}</div><div class="lbl">LOW</div></div>
  <div class="card"><div class="num" style="color:#2B5B84">{by_sev.get('INFO',0)}</div><div class="lbl">INFO</div></div>
</div>

<div class="verdict">
  Status: {badge(verdict, '#B00000' if any(x in str(verdict) for x in ['CRITICAL','DO_NOT']) else '#336633')}
  &nbsp; {cleanup_badge}
  {f'&nbsp; {badge(str(len(jwts))+" JWT VULN","#B00000")}' if any(j.get('severity') in ('CRITICAL','HIGH') for j in jwts) else ''}
  {f'&nbsp; {badge(str(len(cves))+" CVE MATCH","#C05000")}' if cves else ''}
  {f'&nbsp; {badge(str(len([o for o in oauths if o.get("severity") in ("CRITICAL","HIGH")]))+" OAUTH VULN","#B00000")}' if any(o.get('severity') in ('CRITICAL','HIGH') for o in oauths) else ''}
  {f'&nbsp; {badge(str(len(twofas))+" 2FA BYPASS","#B00000")}' if twofas else ''}
  {f'&nbsp; {badge(str(len(blinds))+" BLIND OOB","#C05000")}' if blinds else ''}
  {f'&nbsp; {badge(str(len([t for t in takeovers if t.get("confirmed")]))+" TAKEOVER","#B00000")}' if any(t.get('confirmed') for t in takeovers) else ''}
  {f'&nbsp; {badge(str(len(smugglings))+" SMUGGLING","#B00000")}' if smugglings else ''}
  {f'&nbsp; {badge(str(len(injections))+" SSTI/XXE/LFI","#B00000")}' if injections else ''}
  {f'&nbsp; {badge(str(len(supply_chains))+" DEP CONFUSION","#C05000")}' if supply_chains else ''}
  {f'&nbsp; {badge(str(len(deeplinks))+" DEEPLINK HIJACK","#C05000")}' if deeplinks else ''}
</div>

{diff_summary}

<div class="section">
  <h2>Temuan Kerentanan ({len(findings)} total{f", {len(added_ids)} baru" if added_ids else ""})</h2>
  <table>
    <thead><tr><th>ID</th><th>Judul</th><th>Severity</th><th>Skor</th><th>Status</th></tr></thead>
    <tbody>{finding_rows or '<tr><td colspan=5 style="color:#8A9BAD">Belum ada temuan.</td></tr>'}</tbody>
  </table>
</div>

{f'''<div class="section">
  <h2>Kill Chain / Exploit Chain ({len(chains)})</h2>
  <table><thead><tr><th>ID</th><th>Nama Chain</th><th>Severity</th><th>Status</th></tr></thead>
  <tbody>{chain_rows}</tbody></table>
</div>''' if chains else ''}

{f'''<div class="section">
  <h2>Subdomain Takeover ({len(takeovers)} kandidat)</h2>
  <table><thead><tr><th>ID</th><th>Subdomain</th><th>CNAME</th><th>Layanan</th><th>Status</th></tr></thead>
  <tbody>{''.join(f'<tr><td>{t.get("id","-")}</td><td>{t.get("subdomain","-")}</td><td>{t.get("cname","-")}</td><td>{t.get("service","-")}</td><td>{badge("CONFIRMED","#B00000") if t.get("confirmed") else "kandidat"}</td></tr>' for t in takeovers)}</tbody>
  </table>
</div>''' if takeovers else ''}

{f'''<div class="section">
  <h2>JWT Analysis ({len(jwts)} token)</h2>
  <table><thead><tr><th>ID</th><th>Algoritma</th><th>Severity</th><th>Kerentanan</th></tr></thead>
  <tbody>{jwt_rows}</tbody></table>
</div>''' if jwts else ''}

{f'''<div class="section">
  <h2>OAuth / OIDC ({len(oauths)} finding)</h2>
  <table><thead><tr><th>ID</th><th>Flow</th><th>Severity</th><th>Kerentanan</th></tr></thead>
  <tbody>{''.join(f'<tr><td>{o.get("id","-")}</td><td>{o.get("flow","-")}</td><td>{badge(o.get("severity","HIGH"))}</td><td>{o.get("vulnerability","-")[:70]}</td></tr>' for o in oauths)}</tbody>
  </table>
</div>''' if oauths else ''}

{f'''<div class="section">
  <h2>2FA / OTP Bypass ({len(twofas)} finding)</h2>
  <table><thead><tr><th>ID</th><th>Metode</th><th>Severity</th><th>Kerentanan</th></tr></thead>
  <tbody>{''.join(f'<tr><td>{t.get("id","-")}</td><td>{t.get("method","-")}</td><td>{badge(t.get("severity","HIGH"))}</td><td>{t.get("vulnerability","-")[:70]}</td></tr>' for t in twofas)}</tbody>
  </table>
</div>''' if twofas else ''}

{f'''<div class="section">
  <h2>Blind OOB Vulnerabilities ({len(blinds)} confirmed)</h2>
  <table><thead><tr><th>ID</th><th>Tipe</th><th>Severity</th><th>Canary Callback</th></tr></thead>
  <tbody>{''.join(f'<tr><td>{b.get("id","-")}</td><td>{b.get("type","-")}</td><td>{badge(b.get("severity","HIGH"))}</td><td>{b.get("canary_hit","-")[:70]}</td></tr>' for b in blinds)}</tbody>
  </table>
</div>''' if blinds else ''}

{f'''<div class="section">
  <h2>Business Logic ({len(bizlogics)} finding)</h2>
  <table><thead><tr><th>ID</th><th>Tipe</th><th>Severity</th><th>Temuan</th></tr></thead>
  <tbody>{''.join(f'<tr><td>{b.get("id","-")}</td><td>{b.get("type","-")}</td><td>{badge(b.get("severity","HIGH"))}</td><td>{b.get("finding","-")[:70]}</td></tr>' for b in bizlogics)}</tbody>
  </table>
</div>''' if bizlogics else ''}

{f'''<div class="section">
  <h2>Cache Poisoning ({len(caches)} finding)</h2>
  <table><thead><tr><th>ID</th><th>Tipe</th><th>Severity</th><th>Vector</th></tr></thead>
  <tbody>{''.join(f'<tr><td>{c.get("id","-")}</td><td>{c.get("type","-")}</td><td>{badge(c.get("severity","HIGH"))}</td><td>{c.get("header",c.get("path","-"))[:60]}</td></tr>' for c in caches)}</tbody>
  </table>
</div>''' if caches else ''}

{f'''<div class="section">
  <h2>CVE Matches ({len(cves)} komponen)</h2>
  <table><thead><tr><th>Komponen</th><th>CVE</th><th>CVSS</th><th>Status</th></tr></thead>
  <tbody>{cve_rows}</tbody></table>
</div>''' if cves else ''}

{f'''<div class="section">
  <h2>HTTP Request Smuggling ({len(smugglings)} finding)</h2>
  <table><thead><tr><th>ID</th><th>Variant</th><th>Severity</th><th>Temuan</th></tr></thead>
  <tbody>{''.join(f'<tr><td>{s.get("id","-")}</td><td>{s.get("variant","-")}</td><td>{badge(s.get("severity","CRITICAL"))}</td><td>{s.get("finding","-")[:70]}</td></tr>' for s in smugglings)}</tbody>
  </table>
</div>''' if smugglings else ''}

{f'''<div class="section">
  <h2>Advanced Injection — SSTI / XXE / LFI / Clickjacking ({len(injections)} finding)</h2>
  <table><thead><tr><th>ID</th><th>Tipe</th><th>Severity</th><th>Payload</th><th>Hasil</th></tr></thead>
  <tbody>{''.join(f'<tr><td>{i.get("id","-")}</td><td>{i.get("type","-")}</td><td>{badge(i.get("severity","HIGH"))}</td><td>{i.get("payload","-")[:40]}</td><td>{i.get("finding","-")[:45]}</td></tr>' for i in injections)}</tbody>
  </table>
</div>''' if injections else ''}

{f'''<div class="section">
  <h2>Client-Side — CORS / DNS Rebinding ({len(client_sides)} finding)</h2>
  <table><thead><tr><th>ID</th><th>Tipe</th><th>Severity</th><th>Temuan</th></tr></thead>
  <tbody>{''.join(f'<tr><td>{c.get("id","-")}</td><td>{c.get("type","-")}</td><td>{badge(c.get("severity","HIGH"))}</td><td>{c.get("finding","-")[:70]}</td></tr>' for c in client_sides)}</tbody>
  </table>
</div>''' if client_sides else ''}

{f'''<div class="section">
  <h2>Dependency Confusion ({len(supply_chains)} package)</h2>
  <table><thead><tr><th>ID</th><th>Package</th><th>Registry</th><th>Severity</th><th>Status</th></tr></thead>
  <tbody>{''.join(f'<tr><td>{s.get("id","-")}</td><td>{s.get("package","-")}</td><td>{s.get("registry","-")}</td><td>{badge(s.get("severity","HIGH"))}</td><td>{"🔴 ADA di publik" if s.get("public_exists") else "bersih"}</td></tr>' for s in supply_chains)}</tbody>
  </table>
</div>''' if supply_chains else ''}

{f'''<div class="section">
  <h2>Mobile Deep Link Hijacking ({len(deeplinks)} finding)</h2>
  <table><thead><tr><th>ID</th><th>Tipe</th><th>Scheme</th><th>Severity</th><th>Temuan</th></tr></thead>
  <tbody>{''.join(f'<tr><td>{m.get("id","-")}</td><td>{m.get("type","-")}</td><td>{m.get("scheme","-")}</td><td>{badge(m.get("severity","HIGH"))}</td><td>{m.get("finding","-")[:60]}</td></tr>' for m in deeplinks)}</tbody>
  </table>
</div>''' if deeplinks else ''}

<div class="footer">
  Auto-refresh 10 detik. Tutup browser atau ketik <code>stop hunt</code> di chat untuk menghentikan watch mode.<br>
  Source: pendukung/ai/triage.json &nbsp;|&nbsp; Last updated: {date}
</div>
</body>
</html>"""

    dash_path = os.path.join(root, 'watch-dashboard.html')
    with open(dash_path, 'w', encoding='utf-8') as fh:
        fh.write(html)
    print('DASHBOARD ->', dash_path)


def verify(root, docx=None):
    root = os.path.abspath(root)
    if not docx:
        docs = [f for f in os.listdir(root) if f.endswith('.docx') and not f.startswith('~$')]
        if len(docs) != 1:
            print(f"VERIFY WARNING: expected 1 docx, found {len(docs)}: {docs}")
        docx = os.path.join(root, docs[0]) if docs else None
    if not docx or not os.path.isfile(docx):
        print("VERIFY ERROR: docx file not found")
        return False
    doc = Document(docx)
    text_chunks = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                text_chunks.append(c.text)
    full_text = '\n'.join(text_chunks)
    
    bad_patterns = [
        (re.compile(r'\[REDACTED\]'), 'redaction-marker'),
    ]
    hits = 0
    for pat, label in bad_patterns:
        m = pat.findall(full_text)
        if m:
            print(f"VERIFY FAIL in DOCX: {len(m)} occurrences of {label}")
            hits += len(m)
    if hits == 0:
        print("SCAN DOCX : CLEAN")
    print(f"TOTAL HITS: {hits}")
    return hits == 0
