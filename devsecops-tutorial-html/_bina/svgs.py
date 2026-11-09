# Penjana diagram SVG untuk tutorial bengkel K8s.
# Setiap diagram guna kelas yang sama; warna datang daripada token --d-*.
from xml.sax.saxutils import escape as esc

SVG_RULES = """
.zone{fill:var(--d-zone);stroke:var(--d-line);stroke-width:1.2}
.zone2{fill:var(--d-zone2);stroke:var(--d-line);stroke-width:1.2;stroke-dasharray:6 4}
.box{fill:var(--d-box);stroke:var(--d-line);stroke-width:1.2}
.acc{fill:var(--d-accbg);stroke:var(--d-acc);stroke-width:1.4}
.warn{fill:var(--d-warnbg);stroke:var(--d-warn);stroke-width:1.4}
.okb{fill:var(--d-okbg);stroke:var(--d-ok);stroke-width:1.4}
.solid{fill:var(--d-acc)}
.t{fill:var(--d-fg);font-size:14px}
.th{fill:var(--d-fg);font-size:14px;font-weight:600}
.ts{fill:var(--d-muted);font-size:12px}
.tl{fill:var(--d-muted);font-size:11px;letter-spacing:.06em;text-transform:uppercase;font-weight:600}
.ta{fill:var(--d-acc);font-size:12px;font-weight:600}
.tw{fill:var(--d-warn);font-size:12px;font-weight:600}
.m{font-family:var(--d-mono)}
.arr{fill:none;stroke:var(--d-arrow);stroke-width:1.6}
.arra{fill:none;stroke:var(--d-acc);stroke-width:1.8}
.dash{stroke-dasharray:5 4}
.grid{stroke:var(--d-grid);stroke-width:1}
.area{fill:var(--d-accbg);stroke:var(--d-acc);stroke-width:2}
.head{fill:var(--d-arrow)}
.heada{fill:var(--d-acc)}
text{font-family:var(--d-font)}
"""

LIGHT = dict(zone="#f3f5f8", zone2="#f8f6f1", box="#ffffff", line="#b9c2cf", fg="#18202c",
             muted="#5a6577", acc="#2457c5", accbg="#e6edfb", warn="#b4540b", warnbg="#fbeee2",
             ok="#1f7a4d", okbg="#e3f3ea", arrow="#6b7688", grid="#e1e5eb")
DARK = dict(zone="#1a212c", zone2="#211f1b", box="#121821", line="#3c4757", fg="#e6eaf0",
            muted="#9aa5b6", acc="#7ea4ff", accbg="#1d2a45", warn="#f0a35e", warnbg="#3a2717",
            ok="#5fcf93", okbg="#16301f", arrow="#8b96a8", grid="#2a3340")


def tokens(d):
    return ";".join(f"--d-{k}:{v}" for k, v in d.items())


def standalone_style():
    fonts = "--d-font:'IBM Plex Sans',system-ui,sans-serif;--d-mono:'IBM Plex Mono',ui-monospace,monospace"
    return (f"<style>svg{{{tokens(LIGHT)};{fonts}}}"
            f"@media (prefers-color-scheme:dark){{svg{{{tokens(DARK)}}}}}{SVG_RULES}</style>")


DEFS = ('<defs><marker id="{p}h" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="head"/></marker>'
        '<marker id="{p}a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="heada"/></marker></defs>')


class D:
    def __init__(self, pid, w, h, title, desc):
        self.p, self.w, self.h, self.title, self.desc = pid, w, h, title, desc
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, cls="box", r=8):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" class="{cls}"/>')

    def text(self, x, y, s, cls="t", anchor="start"):
        self.add(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{esc(s)}</text>')

    def node(self, x, y, w, h, title, sub=None, cls="box", tcls="th", mono_sub=False):
        self.rect(x, y, w, h, cls)
        cx = x + w / 2
        if sub:
            self.text(cx, y + h / 2 - 3, title, tcls, "middle")
            self.text(cx, y + h / 2 + 15, sub, "ts m" if mono_sub else "ts", "middle")
        else:
            self.text(cx, y + h / 2 + 5, title, tcls, "middle")

    def path(self, d, acc=False, dash=False, head=True):
        cls = ("arra" if acc else "arr") + (" dash" if dash else "")
        m = f' marker-end="url(#{self.p}{"a" if acc else "h"})"' if head else ""
        self.add(f'<path d="{d}" class="{cls}"{m}/>')

    def svg(self, standalone):
        style = standalone_style() if standalone else ""
        ns = ' xmlns="http://www.w3.org/2000/svg"' if standalone else ""
        return (f'<svg{ns} viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="{self.p}t {self.p}d">'
                f'<title id="{self.p}t">{esc(self.title)}</title><desc id="{self.p}d">{esc(self.desc)}</desc>'
                f'{style}{DEFS.format(p=self.p)}{"".join(self.parts)}</svg>')



def lima_imbasan():
    d = D("li", 900, 330, "Lima jenis imbasan dalam pipeline",
          "Kod, binaan, imej, persekitaran ujian dan produksi, dengan imbasan keselamatan di setiap peringkat: Secret Detection, SAST dan SCA, "
          "IaC dan imbasan imej, DAST, serta admission control.")
    stages = [("Kod", "commit dan PR"), ("Binaan", "CI"), ("Imej", "Dockerfile + registry"), ("Ujian", "app berjalan"), ("Produksi", "kluster")]
    scans = [("Secret Detection", "Gitleaks"), ("SAST · SCA", "Semgrep · Trivy fs"), ("IaC · imej", "Trivy · Checkov · Harbor"),
             ("DAST", "ZAP"), ("Admission", "Kyverno · PSS")]
    d.text(10, 24, "Kos membaiki naik dari kiri ke kanan: imbas seawal mungkin", "tl")
    for i, ((a, b), (s, t)) in enumerate(zip(stages, scans)):
        x = 10 + i * 180
        d.node(x, 50, 160, 64, a, b, "box")
        if i:
            d.path(f"M{x - 20},82 H{x - 1}")
        d.path(f"M{x + 80},114 V176", acc=True)
        d.node(x, 178, 160, 74, s, t, "acc" if i != 3 else "warn")
    d.rect(10, 276, 880, 44, "zone", 8)
    d.text(26, 303, "Setiap imbasan ada pintu (gate): temuan melebihi had akan menggagalkan pipeline sebelum kod bergerak ke peringkat seterusnya.", "ts")
    return d


def dfd_kedai():
    d = D("df", 900, 440, "Gambar rajah aliran data Kedai Bengkel",
          "Pengguna dan admin berada di luar sempadan kepercayaan; app web berada di dalam server bersama pangkalan data SQLite, proses OS untuk ping dan folder files. "
          "Setiap aliran data diberi tag ancaman STRIDE.")
    d.rect(10, 30, 200, 400, "zone2", 12)
    d.text(26, 56, "Di luar kepercayaan", "tl")
    d.rect(270, 30, 620, 400, "zone", 12)
    d.text(286, 56, "Server (sempadan kepercayaan)", "tl")
    d.node(30, 120, 160, 64, "Pengguna", "pelayar", "box")
    d.node(30, 290, 160, 64, "Admin", "cookie sesi", "box")
    d.node(310, 180, 200, 100, "App Kedai Bengkel", "/search /login /guestbook", "acc")
    d.node(690, 80, 180, 56, "Pangkalan data", "SQLite", "box")
    d.node(690, 200, 180, 56, "Proses OS", "ping -c 1 host", "box")
    d.node(690, 320, 180, 56, "Sistem fail", "files/notis.txt", "box")
    d.path("M190,152 H250 V210 H308", acc=True)
    d.text(250, 108, "S · T · R", "tw", "middle")
    d.text(250, 94, "XSS, tiada CSRF", "ts", "middle")
    d.path("M190,322 H250 V252 H308")
    d.text(250, 366, "S · E", "tw", "middle")
    d.text(250, 382, "cookie dipalsukan", "ts", "middle")
    d.path("M510,200 H560 V108 H688", acc=True)
    d.text(600, 96, "T · I: SQL injection", "tw", "middle")
    d.path("M510,230 H688", acc=True)
    d.text(600, 222, "E: command injection", "tw", "middle")
    d.path("M510,262 H560 V348 H688", acc=True)
    d.text(600, 340, "I: path traversal", "tw", "middle")
    d.text(30, 416, "S spoofing · T tampering · R repudiation · I information disclosure · D denial of service · E elevation of privilege", "ts")
    return d


def seni_bina_makmal():
    d = D("sm", 900, 380, "Seni bina makmal",
          "Laptop peserta menjalankan Docker dengan app, kontena imbasan dan kluster k3d; Harbor di server Linode menerima image melalui HTTPS port 443 "
          "dengan CA lab dipercayai dan nama harbor.lab.test dalam fail hosts.")
    d.rect(10, 20, 560, 350, "zone2", 14)
    d.text(26, 46, "Laptop peserta (Docker Desktop · WSL2)", "tl")
    d.node(30, 70, 250, 60, "App lab", "aspnet-app atau laravel-app", "warn")
    d.node(300, 70, 250, 60, "Kontena imbasan", "gitleaks · trivy · semgrep · zap", "acc")
    d.rect(30, 160, 520, 130, "zone", 10)
    d.text(46, 186, "Kluster k3d (satu node, untuk Hari 4)", "th")
    d.node(50, 202, 140, 60, "Kyverno", "dasar admission", "box")
    d.node(210, 202, 140, 60, "Pod app", "securityContext", "okb")
    d.node(370, 202, 160, 60, "NetworkPolicy", "deny by default", "box")
    d.rect(30, 310, 520, 44, "box")
    d.text(46, 337, "hosts: 192.53.174.104 harbor.lab.test · CA lab dipercayai", "ts m")
    d.rect(650, 20, 240, 350, "zone", 14)
    d.text(666, 46, "Server Linode", "tl")
    d.node(670, 70, 200, 64, "Harbor", "harbor.lab.test :443", "acc")
    d.node(670, 160, 200, 56, "Scanner Trivy", "scan automatik semasa push", "box")
    d.node(670, 246, 200, 56, "Projek peserta01…10", "kuota, robot account", "box")
    d.path("M550,100 H668", acc=True)
    d.text(610, 90, "push / pull", "ta", "middle")
    d.text(610, 120, "HTTPS 443", "ts m", "middle")
    d.path("M770,134 V158")
    return d


def aliran_harbor():
    d = D("ah", 900, 300, "Aliran image ke Harbor",
          "Image dibina dan ditolak ke Harbor. Trivy mengimbas secara automatik. Polisi menyekat pull jika ada kerentanan High atau lebih tinggi, "
          "dengan jawapan HTTP 412; image bersih boleh ditarik.")
    d.rect(10, 14, 880, 44, "zone", 8)
    d.text(26, 41, "Perhatian: binaan Docker lalai menambah attestation (OCI index) dan polisi tidak berkuat kuasa. Gunakan --provenance=false.", "ts")
    d.node(10, 90, 120, 64, "docker build", "provenance=false", "box")
    d.node(170, 90, 120, 64, "docker push", "ke peserta01/", "box")
    d.node(330, 90, 140, 64, "Harbor simpan", "projek peserta01", "acc")
    d.node(510, 90, 130, 64, "Trivy imbas", "automatik", "acc")
    d.node(680, 90, 130, 64, "Polisi", "ambang High", "warn")
    d.path("M130,122 H168")
    d.path("M290,122 H328")
    d.path("M470,122 H508")
    d.path("M640,122 H678")
    d.path("M745,154 V196")
    d.path("M745,196 H640")
    d.node(470, 196, 170, 64, "Pull ditolak", "HTTP 412 Precondition Failed", "warn")
    d.path("M810,122 H860 V228 H842")
    d.node(690, 196, 150, 64, "Pull dibenarkan", "tiada High / Critical", "okb")
    return d


def rantaian_bekalan():
    d = D("rb", 900, 230, "Rantaian bekalan perisian",
          "Kod dibina oleh CI, SBOM dijana, image ditandatangani dengan cosign, disimpan di Harbor dan disahkan oleh Kyverno sebelum pod dibenarkan berjalan.")
    steps = [("Kod", "git commit"), ("CI", "build + scan"), ("SBOM", "senarai komponen"), ("Tandatangan", "cosign sign"),
             ("Harbor", "registry"), ("Kyverno", "verify tandatangan"), ("Pod", "berjalan")]
    for i, (a, b) in enumerate(steps):
        x = 8 + i * 126
        cls = "acc" if a in ("SBOM", "Tandatangan", "Kyverno") else "box"
        d.node(x, 70, 112, 64, a, b, cls)
        if i:
            d.path(f"M{x - 14},102 H{x - 1}")
    d.text(10, 34, "Setiap peringkat menambah bukti; peringkat terakhir menolak apa-apa yang tiada bukti.", "ts")
    d.rect(10, 164, 880, 48, "zone", 8)
    d.text(26, 193, "Tanpa tandatangan, sesiapa yang boleh push ke registry boleh menjalankan kod di kluster anda.", "ts")
    return d


def lapisan_hardening():
    d = D("lh", 900, 380, "Lapisan hardening Kubernetes",
          "Empat lapisan bersarang: Kyverno di admission, Pod Security Standards pada namespace, securityContext pada pod dan container, "
          "dengan NetworkPolicy mengawal trafik antara pod.")
    d.rect(10, 20, 880, 350, "zone2", 14)
    d.text(26, 46, "Kluster · Kyverno menolak manifest yang melanggar dasar (admission)", "th")
    d.rect(40, 64, 820, 290, "zone", 12)
    d.text(56, 90, "Namespace · Pod Security Standards: restricted", "th")
    d.rect(70, 108, 520, 230, "box", 10)
    d.text(86, 134, "Pod · securityContext", "th")
    d.node(90, 152, 230, 70, "Container", "runAsNonRoot · readOnlyRootFilesystem", "okb")
    d.node(340, 152, 230, 70, "Container", "drop ALL capabilities", "okb")
    d.text(86, 258, "allowPrivilegeEscalation: false · seccompProfile: RuntimeDefault", "ts m")
    d.text(86, 284, "resources.requests / limits · tiada privileged · tiada hostPath", "ts m")
    d.node(620, 140, 220, 90, "NetworkPolicy", "deny all, benarkan yang perlu", "acc")
    d.path("M590,185 H618")
    d.text(730, 262, "kawal trafik antara pod", "ts", "middle")
    return d


ALL = {
    "lima-imbasan": lima_imbasan, "dfd-kedai": dfd_kedai, "seni-bina-makmal": seni_bina_makmal,
    "aliran-harbor": aliran_harbor, "rantaian-bekalan": rantaian_bekalan, "lapisan-hardening": lapisan_hardening,
}
