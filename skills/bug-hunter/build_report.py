# -*- coding: utf-8 -*-
"""Entrypoint generator laporan Bug Hunter: python build_report.py --root <folder hasil>."""
import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_kit import build, verify

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Bangun satu DOCX Bug Hunter dari pendukung/ai/triage.json')
    ap.add_argument('--root', required=True, help='folder hasil yang berisi pendukung/')
    ap.add_argument('--profile', help='override profil: bughunt|web|apk|all')
    ap.add_argument('--output', help='override path DOCX (misalnya untuk staging saat file asli terkunci)')
    ap.add_argument('--verify', action='store_true', help='hanya verifikasi laporan yang ada')
    a = ap.parse_args()
    if a.verify:
        verify(a.root)
    else:
        out = build(a.root, a.profile, a.output)
        verify(a.root, out)
