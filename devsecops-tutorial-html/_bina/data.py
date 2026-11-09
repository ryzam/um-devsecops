# Data untuk build.py: kapsyen rajah, widget "alat mana tangkap ini?" dan "penjelajah pipeline".
# Semua hasil dalam TOOLDATA daripada ujian sebenar di server lab (kunci jawapan instruktur, tidak diterbitkan).

CAPTIONS = {
    "lima-imbasan": "Lima jenis imbasan dan di mana setiap satu berada dalam perjalanan kod ke produksi.",
    "dfd-kedai": "DFD Kedai Bengkel dengan sempadan kepercayaan dan tag STRIDE pada setiap aliran yang merentas sempadan.",
    "seni-bina-makmal": "Laptop anda menjalankan app, alat imbasan dan kluster k3d; imej dihantar ke Harbor di Linode melalui HTTPS.",
    "aliran-harbor": "Imej ditolak, diimbas secara automatik, dan polisi menyekat pull bagi imej dengan kerentanan High atau lebih tinggi.",
    "rantaian-bekalan": "Setiap peringkat menambah bukti (SBOM, tandatangan) yang disemak oleh Kyverno sebelum pod berjalan.",
    "lapisan-hardening": "Pertahanan berlapis: admission, Pod Security Standards, securityContext dan NetworkPolicy.",
}

INJECT = []

OK, NO, NA = "ok", "no", "na"

TOOLS = [
    {"id": "gitleaks", "name": "Gitleaks"},
    {"id": "trivy", "name": "Trivy"},
    {"id": "semgrep", "name": "Semgrep"},
    {"id": "zap", "name": "ZAP (DAST)"},
    {"id": "sca", "name": "dotnet list / composer audit"},
    {"id": "hadolint", "name": "hadolint"},
    {"id": "checkov", "name": "Checkov"},
    {"id": "kubelinter", "name": "kube-linter"},
    {"id": "manual", "name": "Ujian manual"},
]


def F(fid, trek, name, note, **r):
    return {"id": fid, "t": trek, "name": name, "note": note, "r": r}


FLAWS = [
    # --- Trek A: ASP.NET Core
    F("A1", "a", "SQL injection (carian)", "Rentetan SQL digabung dengan input pengguna.",
      semgrep=(OK, "p/gitlab: SCS0002 (ERROR). Perlu set peraturan gitlab; p/csharp dan p/security-audit tidak menangkap."),
      zap=(OK, "SQL Injection - SQLite, dalam pelan aktif dan API scan."), manual=(OK, "UNION SELECT membaca jadual users.")),
    F("A2", "a", "SQL injection (log masuk)", "admin'-- melepasi semakan kata laluan.",
      semgrep=(OK, "p/gitlab: SCS0002."), zap=(OK, "Pelan aktif sahaja; API scan terlepas."), manual=(OK, "Log masuk sebagai admin tanpa kata laluan.")),
    F("A3", "a", "XSS pantulan", "Input dipantulkan tanpa encoding.",
      semgrep=(NO, "Tiada set peraturan menangkapnya."), zap=(OK, "Pelan aktif: XSS Reflected. API scan terlepas. (DOM XSS dimatikan dalam pelan untuk jimat memori.)"), manual=(OK, "<script> dipantulkan dalam respons.")),
    F("A4", "a", "XSS tersimpan + tiada CSRF", "Buku pelawat menyimpan HTML mentah.",
      semgrep=(NO, "Tidak dikesan."), zap=(OK, "Persistent XSS dan Absence of Anti-CSRF Tokens.")),
    F("A5", "a", "Command injection", "ping dijalankan melalui /bin/sh -c dengan input pengguna.",
      semgrep=(OK, "p/gitlab: SCS0001 (ERROR)."), zap=(OK, "Remote OS Command Injection."), manual=(OK, ";id memulangkan uid=0(root).")),
    F("A6", "a", "Path traversal", "../ keluar dari folder files.",
      semgrep=(NO, "Tidak dikesan."), zap=(OK, "Pelan aktif sahaja."), manual=(OK, "../appsettings.json dibaca.")),
    F("A7", "a", "Open redirect", "Pengalihan ke URL pilihan pengguna.",
      semgrep=(NO, "Tidak dikesan."), zap=(OK, "Off-site Redirect (baseline, full dan API).")),
    F("A8", "a", "Deserialization tidak selamat", "TypeNameHandling.All pada input.",
      semgrep=(OK, "p/default: insecure-newtonsoft-deserialization (WARNING)."), zap=(NO, "Hanya melaporkan CORS pada titik akhir ini.")),
    F("A9", "a", "Cookie sesi boleh dipalsukan", "Peranan dibaca daripada cookie base64.",
      semgrep=(NO, "Logik, bukan corak."), zap=(NO, "Tidak faham logik kebenaran."), manual=(OK, "Cookie palsu membuka panel admin.")),
    F("A10", "a", "IDOR + hash didedahkan", "/api/users/{id} tanpa semakan.",
      semgrep=(NO, "Tidak dikesan."), zap=(NO, "API scan tidak mengesan IDOR."), manual=(OK, "Hash MD5 kata laluan dipulangkan.")),
    F("A11", "a", "MD5 untuk kata laluan", "Hash lemah.",
      semgrep=(NO, "Tiada peraturan menegur MD5 dalam C# pada set yang diuji.")),
    F("A12", "a", "CORS longgar, halaman pengecualian pembangunan, header tiada", "Konfigurasi runtime.",
      semgrep=(OK, "Sebahagian: stacktrace-disclosure pada UseDeveloperExceptionPage sahaja."),
      zap=(OK, "CORS Misconfiguration, CSP, anti-clickjacking, X-Content-Type-Options tiada, Application Error Disclosure.")),
    F("A13", "a", "Secret dalam appsettings.json", "Kata laluan DB, Jwt secret, kunci API palsu.",
      gitleaks=(OK, "generic-api-key (3 dalam fail ini, 1 dalam Dockerfile)."), trivy=(NO, "Pengimbas secret tidak menangkap format palsu."),
      checkov=(OK, "CKV_SECRET_6 (2 temuan).")),
    F("A14", "a", "Secret dalam sejarah git sahaja", "appsettings.Production.json pernah di-commit.",
      gitleaks=(OK, "Hanya dengan 'gitleaks git'. 'gitleaks dir' tidak nampak."), trivy=(NO, "Tidak mengimbas sejarah."),
      checkov=(NO, "Tidak mengimbas sejarah.")),
    F("A15", "a", "Pakej lapuk (Newtonsoft.Json, SharpZipLib) + 2 pakej transitif", "Dua pakej tidak dirancang: Microsoft.OpenApi dan SQLitePCLRaw.",
      sca=(OK, "dotnet list package --vulnerable --include-transitive: 4 pakej."),
      trivy=(OK, "6 CVE, tetapi hanya jika packages.lock.json wujud. Tanpanya: 0.")),
    # --- Trek B: Laravel
    F("B1", "b", "SQL injection (carian)", "DB::select dengan rentetan digabung.",
      semgrep=(NO, "Tiada set peraturan menangkapnya pada PHP/Laravel."), zap=(OK, "Dilaporkan sebagai 'SQL Injection - Oracle' (label salah; pangkalan data ialah SQLite)."),
      manual=(OK, "UNION SELECT memulangkan nama dan hash admin.")),
    F("B2", "b", "SQL injection (log masuk)", "admin'-- melepasi semakan.",
      semgrep=(NO, "Tidak dikesan."), zap=(OK, "SQL Injection."), manual=(OK, "Log masuk sebagai admin.")),
    F("B3", "b", "XSS (Blade {!! !!})", "Output tanpa encoding.",
      semgrep=(NO, "Tidak dikesan."), zap=(OK, "Reflected (pelan aktif).")),
    F("B4", "b", "XSS tersimpan + CSRF dimatikan", "Buku pelawat dan pengecualian CSRF.",
      semgrep=(NO, "Tidak dikesan."), zap=(OK, "Persistent XSS dan Absence of Anti-CSRF Tokens.")),
    F("B5", "b", "Command injection", "shell_exec dengan input pengguna.",
      semgrep=(OK, "p/default dan p/phpcs-security-audit: exec-use."), zap=(OK, "Remote OS Command Injection (juga 'Time Based' pada 4 URL lain, kemungkinan positif palsu)."),
      manual=(OK, ";id memulangkan uid=0(root).")),
    F("B6", "b", "Path traversal", "Fail .env boleh dibaca.",
      semgrep=(NO, "Tidak dikesan."), zap=(OK, "Path Traversal."), manual=(OK, "../.env mendedahkan APP_KEY.")),
    F("B7", "b", "Open redirect", "redirect() dengan URL pengguna.",
      semgrep=(NO, "Tidak dikesan."), zap=(NO, "Tiada pautan ke /redirect, jadi spider tidak jumpa."), manual=(OK, "302 ke laman luar.")),
    F("B8", "b", "Cookie sesi boleh dipalsukan", "Peranan dibaca daripada cookie base64.",
      semgrep=(NO, "Logik."), zap=(NO, "Logik."), manual=(OK, "Cookie palsu membuka panel admin.")),
    F("B9", "b", "IDOR + hash didedahkan", "/api/users/{id}.",
      semgrep=(NO, "Tidak dikesan."), zap=(NO, "Tidak dikesan."), manual=(OK, "Hash MD5 dipulangkan.")),
    F("B10", "b", "Mass assignment", "$guarded = [] membenarkan role=admin.",
      semgrep=(NO, "Tidak dikesan."), zap=(NO, "Tidak dikesan."), manual=(OK, "role=admin menaikkan pengguna.")),
    F("B11", "b", "unserialize() input pengguna", "Boleh mencipta objek sewenang-wenangnya.",
      semgrep=(OK, "p/default: unserialize-use."), zap=(NO, "Tidak dikesan.")),
    F("B12", "b", "MD5 untuk kata laluan", "Hash lemah.",
      semgrep=(OK, "p/phpcs-security-audit: weak-crypto (3 lokasi).")),
    F("B14", "b", "Pakej lapuk (phpmailer 6.4.1, php-jwt 5.0.0)", "Dua pakej dengan kerentanan diketahui.",
      sca=(OK, "composer audit: 4 advisori (1 Critical, 2 High, 1 Low)."), trivy=(OK, "4 CVE daripada composer.lock, tanpa langkah tambahan.")),
    F("B15", "b", "Secret dalam kod dan Dockerfile", "config/kedai.php dan ENV.",
      gitleaks=(OK, "generic-api-key: 4 temuan."), trivy=(NO, "Pengimbas secret tidak menangkap."), checkov=(NO, "Tidak menangkap.")),
    F("B16", "b", "Secret dalam sejarah git (.env)", ".env pernah di-commit.",
      gitleaks=(OK, "Hanya 'gitleaks git' (3 temuan)."), trivy=(NO, "Tidak mengimbas sejarah.")),
    # --- IaC (kedua-dua trek)
    F("I1", "x", "Dockerfile: root, tiada HEALTHCHECK, apt tanpa pin", "Imej SDK sebagai runtime.",
      trivy=(OK, "DS-0002 (HIGH, root), DS-0029 (HIGH), DS-0026 (LOW, tiada HEALTHCHECK)."),
      hadolint=(OK, "DL3008, DL3009, DL3015. TIDAK menegur ketiadaan USER atau HEALTHCHECK."),
      checkov=(OK, "CKV_DOCKER_2 (HEALTHCHECK) dan CKV_DOCKER_3 (USER).")),
    F("I2", "x", "Secret dalam ENV Dockerfile", "ENV Jwt__Secret / PAYMENT_API_KEY.",
      gitleaks=(OK, "generic-api-key."), trivy=(OK, "Peraturan config DS-0031 (CRITICAL); pengimbas secret tidak."),
      hadolint=(OK, "DL3064."), checkov=(NO, "Tidak menegur.")),
    F("I3", "x", "K8s: privileged, root, hostNetwork, docker.sock, :latest", "Manifest tidak selamat.",
      trivy=(OK, "21 temuan setiap fail (KSV-*)."), checkov=(OK, "21 kegagalan setiap fail."),
      kubelinter=(OK, "10 (aspnet) dan 9 (laravel): docker-sock, host-network, privileged-container, latest-tag dll.")),
    F("I4", "x", "K8s: secret dalam env", "name/value pada baris berasingan.",
      gitleaks=(NO, "Peraturan lalai terlepas; peraturan custom menangkapnya."), trivy=(NO, "Tidak menegur."),
      checkov=(NO, "Tidak menegur."), kubelinter=(OK, "env-var-secret menangkap Jwt__Secret tetapi bukan PAYMENT_API_KEY (bergantung pada nama).")),
    F("I5", "x", "Terraform: S3 awam, SSH terbuka, RDS awam tanpa penyulitan", "terraform/main.tf.",
      trivy=(OK, "18 temuan, AWS-0104 CRITICAL."), checkov=(OK, "21 kegagalan + CKV_SECRET_6."),
      gitleaks=(OK, "Kata laluan RDS (generic-api-key).")),
]

TOOLDATA = {"tools": TOOLS, "flaws": FLAWS}

# Penjelajah pipeline: setiap peringkat dengan alat, arahan, syarat gagal dan masa yang diukur di server lab.
PIPEDATA = [
    {"name": "1 · Pre-commit", "rows": [
        ["Alat", "Gitleaks (mod pre-commit)"],
        ["Arahan", "<code>gitleaks git --pre-commit --staged --redact</code>"],
        ["Gagal bila", "Ada secret dalam perubahan yang dipentaskan (exit 1)"],
        ["Masa diukur", "Kurang 1 saat"],
        ["Had", "Boleh dielak dengan <code>--no-verify</code>; imbasan CI ialah jaring sebenar"]]},
    {"name": "2 · Pull request", "rows": [
        ["Alat", "Gitleaks (sejarah), Semgrep (SAST), Trivy fs (SCA)"],
        ["Arahan", "<code>gitleaks git .</code> · <code>semgrep scan --config p/default --config p/gitlab</code> · <code>trivy fs --severity HIGH,CRITICAL --exit-code 1 .</code>"],
        ["Gagal bila", "Secret baharu (selepas baseline), temuan Semgrep ERROR, kerentanan High/Critical dalam pakej"],
        ["Masa diukur", "Gitleaks 0.7 s · Semgrep 7.5 s · Trivy fs 1 s"],
        ["Nota", "Semgrep: set peraturan menentukan apa yang dilihat. Trivy memerlukan <code>packages.lock.json</code> (.NET)."]]},
    {"name": "3 · Binaan imej", "rows": [
        ["Alat", "hadolint, Trivy config, Checkov, kemudian Trivy image"],
        ["Arahan", "<code>hadolint Dockerfile</code> · <code>trivy config --exit-code 1 --severity HIGH,CRITICAL .</code> · <code>trivy image --exit-code 1 --severity CRITICAL IMEJ</code>"],
        ["Gagal bila", "Dockerfile/manifest melanggar peraturan, atau imej ada kerentanan Critical"],
        ["Masa diukur", "Binaan .NET 33 s · trivy config 1.5 s · trivy image 15 s · Checkov 9.5 s · hadolint 0.4 s"],
        ["Nota", "Bina dengan <code>--provenance=false --sbom=false</code> supaya polisi Harbor berkuat kuasa."]]},
    {"name": "4 · Registry (Harbor)", "rows": [
        ["Alat", "Harbor + Trivy terbina dalam"],
        ["Arahan", "<code>docker push harbor.lab.test/pesertaNN/app:tag</code>"],
        ["Gagal bila", "Pull ditolak (HTTP 412) jika ada kerentanan pada atau melebihi ambang projek (High)"],
        ["Masa diukur", "Imbasan automatik selesai dalam kira-kira 10 saat bagi imej kecil; beberapa puluh saat bagi imej besar"],
        ["Nota", "Polisi menghalang <b>pull</b>, bukan <b>push</b>. Imej yang dibina dengan attestation (OCI index) terlepas polisi."]]},
    {"name": "5 · Persekitaran ujian", "rows": [
        ["Alat", "ZAP (baseline, pelan aktif, API)"],
        ["Arahan", "<code>zap-baseline.py -t URL</code> · <code>zap.sh -cmd -autorun zap-plan.yaml</code> · <code>zap-api-scan.py -t openapi.json -f openapi</code>"],
        ["Gagal bila", "Peraturan yang ditetapkan FAIL dalam fail konfigurasi (baseline exit 1); tanpa itu amaran memberi exit 2"],
        ["Masa diukur", "Baseline ≈ 35 s · pelan aktif ≈ 90 s (ASP.NET) dan ≈ 100 s (Laravel) · API ≈ 40 s. Memori puncak ≈ 0.8 GB dengan pelan; <code>zap-full-scan.py</code> memakai hingga 4.4 GB"],
        ["Nota", "Baseline (pasif) terlepas hampir semua kelemahan sebenar. Jalankan aktif pada app ujian sahaja, bukan produksi. Had memori 2 GB pada kontena."]]},
    {"name": "6 · Admission", "rows": [
        ["Alat", "Pod Security Standards + Kyverno"],
        ["Arahan", "<code>kubectl label ns lab pod-security.kubernetes.io/enforce=restricted</code> · ClusterPolicy Kyverno (tag, registry, tandatangan cosign)"],
        ["Gagal bila", "Manifest ditolak oleh API server: privileged, root, tag :latest, imej tanpa tandatangan"],
        ["Masa diukur", "Serta-merta pada <code>kubectl apply</code>; kluster k3d siap dalam ≈ 30 s (≈ 0.4 GB, ≈ 1.2 GB dengan Kyverno)"],
        ["Nota", "Lapisan terakhir: menolak apa yang terlepas daripada semua imbasan sebelumnya."]]},
]
