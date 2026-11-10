# Bina laman HTML interaktif daripada ../../devsecops-tutorial (relatif kepada skrip ini; sumber tidak diubah).
# Guna: python devsecops-tutorial-html/_bina/build.py [folder-output]
import html, json, os, re, sys, textwrap
INDENTED = []
import markdown
sys.path.insert(0, os.path.dirname(__file__))
import svgs
import data

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # folder yang mengandungi devsecops-tutorial/
SRC = os.environ.get("BENGKEL_SRC", os.path.join(ROOT, "devsecops-tutorial"))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "devsecops-tutorial-html")
HERE = os.path.dirname(__file__)

MODULES = [  # (id, dir, nav label, eyebrow)
    ("gambaran", "", "Gambaran bengkel", "Mula di sini"),
    ("persediaan", "00-persediaan", "Persediaan · Alat dan akses", "Sebelum Hari 1 · semua peserta"),
    ("m0", "modul-0-pengenalan", "Modul 0 · Pengenalan dan threat modeling", "Hari 1 · 9:00 pagi – 1:00 petang"),
    ("m1", "modul-1-secret", "Modul 1 · Secret Detection", "Hari 1 · 2:00 – 5:00 petang"),
    ("m2", "modul-2-sast", "Modul 2 · SAST", "Hari 2 · 9:00 pagi – 1:00 petang"),
    ("m3", "modul-3-sca", "Modul 3 · SCA dan SBOM", "Hari 2 · 2:00 – 5:00 petang"),
    ("m4", "modul-4-container-iac", "Modul 4 · Container, Harbor dan IaC", "Hari 3 · 9:00 pagi – 1:00 petang"),
    ("m5", "modul-5-dast", "Modul 5 · DAST", "Hari 3 · 2:00 – 5:00 petang"),
    ("m6", "modul-6-cicd", "Modul 6 · CI/CD dan supply chain", "Hari 4 · 9:00 pagi – 1:00 petang"),
    ("m7", "modul-7-hardening", "Modul 7 · Hardening K8s dan capstone", "Hari 4 · 2:00 – 5:00 petang"),
]
DIR2ID = {d: i for i, d, _, _ in MODULES}

CAPTIONS = data.CAPTIONS

# Blok teks yang digantikan oleh SVG: penanda -> nama diagram (kosong; semua rajah disuntik)
ASCII = []
# Diagram dan widget disuntik sebelum tajuk tertentu: (modul, tajuk, sisipan)
INJECT = data.INJECT


def slug(s):
    s = re.sub(r"<[^>]+>", "", html.unescape(s)).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def file_id(path):
    return "f-" + slug(path)


def prep_md(mid, text):
    def fence(m):
        body = m.group(2)
        for mark, name in ASCII:
            if mark in body and ("─" in body or "│" in body or "+" in body):
                return f'\n<div data-fig="{name}"></div>\n'
        return m.group(0)
    text = re.sub(r"^```(\w*)\n(.*?)^```", fence, text, flags=re.S | re.M)
    for m, head, ins in INJECT:
        if m == mid:
            assert head in text, (mid, head)
            text = text.replace(head, ins + "\n\n" + head, 1)
    text = text.replace("<details>", '<details markdown="1">')

    # fence berinden dalam senarai: Python-Markdown tidak menyokongnya, jadi simpan dan sisip semula
    def indented(m):
        INDENTED.append((m.group(2), textwrap.dedent(m.group(3))))
        return f"{m.group(1)}CODEBLOCK{len(INDENTED) - 1}X"
    text = re.sub(r"^( +)```(\w*)\n(.*?)^ +```", indented, text, flags=re.S | re.M)
    return text


def fig_html(name):
    d = svgs.ALL[name]()
    return (f'<figure class="fig" id="fig-{name}"><div class="fig-scroll">{d.svg(False)}</div>'
            f'<figcaption><span>{html.escape(CAPTIONS[name])}</span>'
            f'<a class="svg-link" href="svg/{name}.svg">SVG</a></figcaption></figure>')


WIDGETS = {
    "alat": """<section class="widget" aria-labelledby="w-alat-t"><h4 id="w-alat-t">Alat mana menangkap vulnerability ini?</h4>
<p class="wnote">Pilih satu vulnerability yang ditanam dalam app lab. Hasilnya daripada ujian sebenar di server lab (trek yang anda pilih di menu kiri menentukan app yang dipaparkan).</p>
<label class="wgrid" style="display:block"><select id="wt-sel" class="wsel" aria-label="Pilih vulnerability"></select></label>
<p class="wnote" id="wt-note" style="margin-top:10px"></p>
<div class="wtool" id="wt-out"></div></section>""",
    "pipeline": """<section class="widget" aria-labelledby="w-pipe-t"><h4 id="w-pipe-t">Penjelajah pipeline</h4>
<p class="wnote">Klik satu peringkat untuk lihat alat, arahan, syarat gagal dan kos masa.</p>
<div class="wsteps" id="wp-steps"></div><div class="wdetail" id="wp-out" aria-live="polite"></div></section>""",
}


def rewrite_links(mid, mdir, h):
    def fix(m):
        href = m.group(1)
        if re.match(r"https?://", href):
            return f'href="{href}" target="_blank" rel="noopener"'
        if href.startswith("#"):
            return f'href="#{mid}-{href[1:]}"'
        href, _, frag = href.partition("#")
        p = os.path.normpath(os.path.join(mdir, href)) if mdir else os.path.normpath(href)
        if p.endswith("README.md"):
            tid = DIR2ID.get(os.path.dirname(p), "gambaran")
            return f'href="#{tid}-{frag}"' if frag else f'href="#{tid}"'
        return f'href="#{file_id(p)}"'
    return re.sub(r'href="([^"]+)"', fix, h)


def code_block(lang, body, escaped=False):
    if not escaped:
        body = html.escape(body.rstrip("\n") + "\n", quote=False)
    label = {"bash": "terminal", "powershell": "powershell", "": "teks"}.get(lang, lang)
    cls = f' class="language-{lang}"' if lang in ("bash", "yaml", "python", "javascript", "json", "csharp", "php", "dockerfile", "powershell", "ini", "xml", "hcl") else ' class="nohighlight"'
    return (f'<div class="code"><div class="code-bar"><span>{label}</span>'
            f'<button type="button" class="copy">Salin</button></div><pre><code{cls}>{body}</code></pre></div>')


def post(mid, mdir, h, sec):
    h = rewrite_links(mid, mdir, h)

    def head(m):
        lvl, inner = m.group(1), m.group(2)
        hid = f"{mid}-{slug(inner)}"
        if lvl in ("2", "3"):
            sec.append((hid, re.sub(r"<[^>]+>", "", inner), lvl))
        extra = ""
        if lvl == "2" and inner.startswith("Makmal"):
            extra = (f'<label class="done-toggle"><input type="checkbox" data-k="{hid}" data-m="{mid}">'
                     f'<span>Selesai</span></label>')
        return f'<h{lvl} id="{hid}"><a class="hl" href="#{hid}">{inner}</a>{extra}</h{lvl}>'
    h = re.sub(r"<h([1-4])>(.*?)</h\1>", head, h)
    n = [0]

    def chk(m):
        n[0] += 1
        return (f'<li class="task"><label><input type="checkbox" data-k="{mid}-semak-{n[0]}" data-m="{mid}">'
                f'<span>{m.group(1)}</span></label></li>')
    h = re.sub(r"<li>\[ \] (.*?)</li>", chk, h, flags=re.S)

    def code(m):
        return code_block(m.group(1) or "", m.group(2), escaped=True)
    h = re.sub(r'<pre><code(?: class="language-(\w+)")?>(.*?)</code></pre>', code, h, flags=re.S)
    h = re.sub(r"(?:<p>)?CODEBLOCK(\d+)X(?:</p>)?", lambda m: code_block(*INDENTED[int(m.group(1))]), h)
    h = re.sub(r"<table>", '<div class="tbl"><table>', h).replace("</table>", "</table></div>")
    h = re.sub(r'<div data-fig="([\w-]+)"></div>', lambda m: fig_html(m.group(1)), h)
    h = re.sub(r'<div data-widget="(\w+)"></div>', lambda m: WIDGETS[m.group(1)], h)
    # fail yang dipaparkan terus dalam teks: <div data-file="modul/fail.ext"></div> (laluan relatif kepada sumber)
    h = re.sub(r'<div data-file="([^"]+)"></div>',
               lambda m: file_block(m.group(1), os.path.basename(m.group(1)), "-sisip"), h)
    return h


LANG = {".yaml": "yaml", ".yml": "yaml", ".py": "python", ".js": "javascript", ".json": "json", ".sh": "bash",
        ".ps1": "powershell", ".toml": "ini", ".tf": "hcl", ".cs": "csharp", ".php": "php", ".csproj": "xml",
        ".crt": "", ".md": ""}


def file_block(rel, short, suffix=""):
    """Satu fail sebagai blok <details> yang boleh dibuka dan disalin. `suffix` mengelakkan id berganda
    apabila fail yang sama dipaparkan di dua tempat (dalam teks dan dalam 'Fail modul')."""
    txt = open(os.path.join(SRC, rel), encoding="utf-8").read()
    ext = os.path.splitext(rel)[1]
    lang = LANG.get(ext, "")
    cls = f"language-{lang}" if lang else "nohighlight"
    size = len(txt.encode())
    sz = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
    return (f'<details class="file" id="{file_id(rel)}{suffix}"><summary><span class="fname">{html.escape(short)}</span>'
            f'<span class="fsize">{sz}</span></summary><div class="code"><div class="code-bar"><span>{lang or "teks"}</span>'
            f'<button type="button" class="copy">Salin</button></div><pre><code class="{cls}">{html.escape(txt)}</code></pre></div></details>')


def files_html(mid, mdir):
    root = os.path.join(SRC, mdir)
    items = []
    for dp, dn, fn in os.walk(root):
        dn.sort()
        if dp != root and (os.path.basename(dp).startswith("modul-") or os.path.relpath(dp, SRC) in DIR2ID):
            dn[:] = []
            continue
        for f in sorted(fn):
            rel = os.path.relpath(os.path.join(dp, f), SRC)
            if f == "README.md" or (mdir == ""):
                continue
            items.append(rel)
    if not items:
        return ""
    out = [f'<section class="files" id="{mid}-fail"><h2><a class="hl" href="#{mid}-fail">Fail modul</a></h2>'
           f'<p class="wnote">Semua fail dan skrip untuk modul ini. Klik untuk buka, kemudian salin.</p>']
    for rel in items:
        out.append(file_block(rel, os.path.relpath(rel, mdir)))
    out.append("</section>")
    return "\n".join(out)


def build():
    os.makedirs(os.path.join(OUT, "svg"), exist_ok=True)
    for name, fn in svgs.ALL.items():
        with open(os.path.join(OUT, "svg", f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(fn().svg(True))
    sections, nav = [], []
    for mid, mdir, label, eyebrow in MODULES:
        text = open(os.path.join(SRC, mdir, "README.md"), encoding="utf-8").read()
        md = markdown.Markdown(extensions=["fenced_code", "tables", "md_in_html"])
        h = md.convert(prep_md(mid, text))
        sec = []
        h = post(mid, mdir, h, sec)
        h = re.sub(r'<h1 id="[^"]+"><a class="hl" href="#[^"]+">(.*?)</a></h1>',
                   lambda m: f'<header class="mod-head"><p class="eyebrow">{eyebrow}</p><h1>{m.group(1)}</h1>'
                             f'<div class="mod-prog" data-m="{mid}"><span class="bar"><i></i></span><span class="lbl"></span></div></header>',
                   h, count=1)
        fh = files_html(mid, mdir) if mdir else ""
        if fh:
            sec.append((f"{mid}-fail", "Fail modul", "2"))
        sections.append(f'<section class="module" id="{mid}" data-m="{mid}">{h}{fh}</section>')
        sub = "".join(f'<li class="l{lv}"><a href="#{i}">{html.escape(html.unescape(t))}</a></li>' for i, t, lv in sec)
        nav.append(f'<li class="nav-mod" data-m="{mid}"><div class="nav-row"><a class="nav-top" href="#{mid}"><span>{label}</span>'
                   f'<span class="nav-count" data-m="{mid}"></span></a>'
                   f'<button type="button" class="nav-exp" aria-expanded="false" aria-label="Tunjuk sub-bahagian {html.escape(label)}">'
                   f'<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>'
                   f'</button></div><ul>{sub}</ul></li>')
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    datablock = ("<script>window.__TOOLDATA=" + json.dumps(data.TOOLDATA, ensure_ascii=False).replace("</", "<\\/") +
                 ";window.__PIPEDATA=" + json.dumps(data.PIPEDATA, ensure_ascii=False).replace("</", "<\\/") + ";</script>\n")
    tpl = tpl.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js', datablock + '<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js', 1)
    page = (tpl.replace("{{SVG_RULES}}", svgs.SVG_RULES)
               .replace("{{LIGHT}}", svgs.tokens(svgs.LIGHT)).replace("{{DARK}}", svgs.tokens(svgs.DARK))
               .replace("{{NAV}}", "\n".join(nav)).replace("{{CONTENT}}", "\n".join(sections)))
    full = ('<!doctype html>\n<html lang="ms">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + page.replace("<div class=\"layout\">", "</head>\n<body>\n<div class=\"layout\">", 1) + "\n</body>\n</html>\n")
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(full)
    with open(os.path.join(HERE, "artifact.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("ok", len(page))


build()
