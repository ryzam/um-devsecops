# Cara bina semula tutorial

Tutorial HTML dibina daripada Markdown dalam `devsecops-tutorial/` (relatif kepada folder ini). Fail `index.html` ialah satu fail yang berdiri sendiri (kecuali fon Google dan highlight.js dari CDN).

```bash
pip install markdown
python devsecops-tutorial-html/_bina/build.py
```

- Sumber: `devsecops-tutorial/<modul>/README.md`; fail dalam folder modul (skrip, YAML, tampalan) dipaparkan automatik di bahagian "Fail modul".
- Data widget dan rajah: `_bina/data.py` (hasil ujian setiap alat, penjelajah pipeline, kapsyen) dan `_bina/svgs.py` (rajah).
- Pilihan trek: bungkus kandungan dalam `<div class="trk trk-a" markdown="1">` (ASP.NET) atau `<div class="trk trk-b" markdown="1">` (Laravel). Elakkan `##`/`###` di dalamnya (tajuk masuk menu kiri).
- Pratonton setempat: `python -m http.server 8765 --bind 127.0.0.1` dalam folder `devsecops-tutorial-html`, kemudian buka <http://127.0.0.1:8765/index.html>.
