# Modul 5: DAST

**Hari 3, 2:00 hingga 5:00 petang**

Dalam modul ini anda akan:

1. Faham beza DAST dan SAST, dan beza antara imbasan **pasif** dan **aktif**.
2. Menjalankan **ZAP** (Zed Attack Proxy, dahulu dikenali sebagai OWASP ZAP) dalam tiga mod (baseline, imbasan aktif ringan, dan API) terhadap app anda yang sedang berjalan.
3. Membandingkan hasil DAST dengan SAST dan threat model, termasuk apa yang DAST **terlepas**.
4. Membaiki XSS, path traversal, open redirect, header keselamatan (dan CSRF pada Laravel), kemudian mengesahkan dengan imbasan semula.
5. Menetapkan **quality gate** DAST melalui exit code dan fail konfigurasi.

> Prasyarat: [Modul 4](../modul-4-container-iac/README.md) siap; `alat.sh` terkini (fungsi `zap` membawa had memori). Imej `aspnet-app:latest` atau `laravel-app:latest` daripada Modul 0 masih ada (ia mengandungi kod asal yang rentan).

> **Amaran.** Jangan sekali-kali menjalankan imbasan aktif terhadap sistem yang bukan milik anda tanpa kebenaran bertulis. Imbasan aktif menghantar muatan serangan sebenar dan boleh mengubah data, menyebabkan ralat atau menjatuhkan app. Lakukan hanya terhadap app ujian.

## Jadual

| Masa | Aktiviti |
|---|---|
| 2:00 – 2:30 | Teori: DAST, mod ZAP, had |
| 2:30 – 3:15 | Makmal 5.1 dan 5.2: jalankan app, imbasan baseline |
| 3:15 – 3:30 | Rehat |
| 3:30 – 4:00 | Makmal 5.3 dan 5.4: imbasan aktif dan API |
| 4:00 – 4:45 | Makmal 5.5 dan 5.6: bandingkan, baiki, imbas semula |
| 4:45 – 5:00 | Makmal 5.7: quality gate dan semakan |

---

## Teori ringkas

### DAST dan SAST

**DAST** (Dynamic Application Security Testing) menyerang app yang **sedang berjalan** dari luar seperti penyerang, tanpa melihat kod. Ia menemui masalah yang SAST tidak nampak: konfigurasi runtime (header, CORS), kelemahan yang bergantung pada cara pelayan sebenarnya menjawab, dan bukti bahawa sesuatu **boleh dieksploit**.

| | SAST | DAST |
|---|---|---|
| Melihat | Kod sumber | App yang berjalan |
| Bila | Awal, setiap commit | Lewat, perlu app berjalan |
| Menunjuk | Baris kod | URL dan parameter |
| Kekuatan | Pantas, tepat pada kod | Bukti eksploit, konfigurasi runtime |
| Kelemahan | Tidak nampak runtime | Hanya nampak apa yang ia **jumpa** (liputan) |

### Pasif dan aktif

- **Pasif**: ZAP hanya **memerhati** permintaan dan jawapan biasa, dan menegur apa yang kelihatan (header tiada, cookie tanpa bendera). Selamat dan pantas, tetapi tidak menemui kelemahan yang perlu diserang untuk dilihat.
- **Aktif**: ZAP **menghantar muatan serangan** (cuba suntikan SQL, skrip, laluan `../`) dan memerhati reaksi. Ia menemui kelemahan sebenar tetapi lebih perlahan, boleh mengubah data, dan perlu dijalankan pada persekitaran ujian.

### Mod ZAP yang kita guna

| Mod | Arahan | Fungsi |
|---|---|---|
| Baseline | `zap-baseline.py` | Spider ringkas + imbasan pasif. Selamat untuk CI |
| Pelan aktif | `zap.sh -cmd -autorun pelan.yaml` | Spider + imbasan aktif, dikawal melalui fail YAML |
| API | `zap-api-scan.py -f openapi` | Menyerang titik akhir yang disenaraikan dalam dokumen OpenAPI |

ZAP juga ada `zap-full-scan.py` (imbasan aktif penuh). Dalam ujian kami ia memakai **hingga 4.4 GB RAM** kerana peraturan DOM XSS menggunakan pelayar tanpa kepala, dan ia mengambil masa lebih lama. Itu terlalu berat untuk laptop 8 GB, jadi kita guna **pelan aktif** yang mematikan peraturan DOM XSS (lihat `zap-plan.yaml` dalam **Fail modul**). Fungsi `zap` dalam `alat.sh` juga menghadkan kontena kepada 2 GB.

### Liputan: apa yang tidak dijumpai tidak diuji

DAST hanya menyerang halaman yang ia **jumpa**. Spider mengikut pautan; halaman yang tiada pautan, titik akhir API tanpa dokumentasi, dan halaman di sebalik log masuk mungkin tidak disentuh. Satu temuan "bersih" tidak bermakna app bersih; ia bermakna **apa yang ZAP capai** bersih.

---

## Makmal 5.1: Jalankan app pada rangkaian imbasan

**Tujuan.** ZAP berjalan dalam kontena dan mencapai app melalui nama. Kedua-duanya mesti berada dalam satu rangkaian Docker.

<div class="trk trk-a" markdown="1">

```bash
source alat.sh
docker network create dast 2>/dev/null
docker rm -f kedai 2>/dev/null
docker run -d --name kedai --network dast aspnet-app:latest
sleep 6
docker run --rm --network dast curlimages/curl -s -o /dev/null -w "%{http_code}\n" http://kedai:8080/
```

</div>

<div class="trk trk-b" markdown="1">

```bash
source alat.sh
docker network create dast 2>/dev/null
docker rm -f kedai 2>/dev/null
docker run -d --name kedai --network dast laravel-app:latest
sleep 10
docker run --rm --network dast curlimages/curl -s -o /dev/null -w "%{http_code}\n" http://kedai:8080/
```

</div>

Jawapan `200` bermakna app boleh dicapai. Simpan skrip `ringkas-zap.py` (**Fail modul**) dalam folder repo: ia meringkaskan laporan ZAP.

---

## Makmal 5.2: Imbasan baseline (pasif)

**Tujuan.** Lihat apa yang pasif sahaja temui.

```bash
zap zap-baseline.py -t http://kedai:8080 -J baseline.json -r baseline.html -I -m 1
python3 ringkas-zap.py zap-hasil/baseline.json
```

`-m 1` mengehadkan spider kepada 1 minit, `-I` bermaksud jangan gagalkan pada amaran, `-J` dan `-r` menulis laporan JSON dan HTML ke `zap-hasil/`. Buka `zap-hasil/baseline.html` dalam pelayar untuk laporan penuh.

Soalan: adakah baseline menemui SQL injection atau XSS?

<details>
<summary>Jawapan jangkaan</summary>

<div class="trk trk-a" markdown="1">

**13 jenis isyarat**: 1 Tinggi (**Off-site Redirect**), 3 Sederhana (CSP tiada, anti-clickjacking tiada, anti-CSRF tiada) dan selebihnya Rendah/Maklumat. Tiada SQL injection, XSS atau command injection: kerana baseline tidak menyerang.
</div>

<div class="trk trk-b" markdown="1">

**15 jenis isyarat**, 0 Tinggi dan 3 Sederhana (CSP, anti-clickjacking, anti-CSRF). Tiada SQL injection, XSS atau command injection.
</div>

Baseline mengambil **kira-kira 35 saat**. Ia sesuai untuk CI kerana pantas dan selamat, tetapi ia **tidak menggantikan** imbasan aktif.
</details>

---

## Makmal 5.3: Imbasan aktif (pelan)

**Tujuan.** Serang app dengan sebenar-benarnya, dengan penggunaan memori yang terkawal.

Simpan `zap-plan.yaml` (**Fail modul**) dalam folder repo, salin ke `zap-hasil/`, dan jalankan:

```bash
cp zap-plan.yaml zap-hasil/
zap zap.sh -cmd -autorun /zap/wrk/zap-plan.yaml
python3 ringkas-zap.py zap-hasil/pelan.json
```

Buka `zap-plan.yaml` dan baca: satu **spider** (1 minit), imbasan pasif, satu **imbasan aktif** (had 4 minit) dengan peraturan DOM XSS dimatikan, dan satu laporan. Perhatikan komen yang menerangkan **kenapa** peraturan dimatikan.

Sementara menunggu, buka terminal kedua dan lihat penggunaan memori: `docker stats --no-stream`.

<details>
<summary>Jawapan jangkaan</summary>

<div class="trk trk-a" markdown="1">

**≈ 18 jenis isyarat** dalam **≈ 90 saat**, memori puncak **≈ 0.8 GB**. Tinggi: XSS (pantulan dan tersimpan), SQL injection (`/login` dan `/search`), command injection (`/ping`, juga varian time-based), path traversal (`/download`), dan open redirect (`/redirect`). Sederhana: anti-CSRF tiada, CSP tiada, anti-clickjacking tiada, CORS yang terlalu longgar.
</div>

<div class="trk trk-b" markdown="1">

**≈ 17 jenis isyarat** dalam **≈ 100 saat**, memori puncak **≈ 0.8 GB**. Tinggi: XSS (pantulan dan tersimpan), SQL injection (`/login`, dan `/search` yang dilabel secara salah sebagai "Oracle" walaupun pangkalan datanya SQLite), command injection dan path traversal. Open redirect **tidak** dijumpai: tiada pautan ke `/redirect` dalam halaman dan tiada dokumen OpenAPI, jadi spider tidak tahu ia wujud.
</div>

Perhatikan juga isyarat **Time Based** command injection yang dilaporkan pada URL selain `/ping`. Itu kemungkinan besar positif palsu: muatan `sleep` memperlahankan app, dan ZAP tersalah anggap respons yang perlahan sebagai bukti. Sahkan sebelum percaya.
</details>

---

## Makmal 5.4: Imbasan API dan liputan

<div class="trk trk-a" markdown="1">

**Tujuan.** App anda menerbitkan dokumen OpenAPI. ZAP boleh menggunakannya untuk menyerang setiap titik akhir yang disenaraikan, termasuk yang tidak ada pautan.

```bash
docker run --rm --network dast curlimages/curl -s -o /dev/null -w "dokumen OpenAPI: %{http_code}\n" http://kedai:8080/openapi/v1.json
zap zap-api-scan.py -t http://kedai:8080/openapi/v1.json -f openapi -O http://kedai:8080 -J api.json -I -T 3
python3 ringkas-zap.py zap-hasil/api.json
```

Bandingkan dengan Makmal 5.3: isyarat apa yang muncul di sini tetapi tidak di sana, dan sebaliknya?

<details>
<summary>Jawapan</summary>

Imbasan API selesai dalam **≈ 40 saat** dan menemui **20 jenis isyarat** (4 Tinggi): redirect (`/redirect`), command injection (`/ping`) dan SQL injection (`/search`). Ia **tidak** menemui XSS, SQL injection `/login` atau path traversal yang pelan aktif temui. Setiap mod menemui subset yang berbeza: gabungkan, jangan pilih satu.

Imbasan API juga menyebabkan `POST /guestbook` dan `POST /login` memberi ralat HTTP 500 (permintaan tanpa badan borang): satu lagi tanda bahawa app tidak mengendalikan input tidak sah dengan baik.
</details>

</div>

<div class="trk trk-b" markdown="1">

**Tujuan.** Memahami bahawa DAST hanya menyerang apa yang ia jumpa.

App Laravel anda tidak menerbitkan dokumen OpenAPI, jadi tiada imbasan API. Sebaliknya, bandingkan apa yang spider jumpa dengan apa yang sebenarnya wujud:

```bash
grep -oE "Route::(get|post)\('[^']+'" laravel-app/routes/web.php | sort -u
python3 - <<'EOF'
import json
d = json.load(open("zap-hasil/pelan.json"))
urls = sorted({i["uri"].split("?")[0].replace("http://kedai:8080", "") or "/" for s in d["site"] for a in s["alerts"] for i in a["instances"]})
print("URL dalam laporan ZAP:", urls)
EOF
```

<details>
<summary>Jawapan</summary>

Laluan seperti `/redirect`, `/admin`, `/api/users/{id}`, `/api/profile/{id}` dan `/api/import` wujud dalam kod tetapi **tiada dalam laporan** (atau tidak disentuh dengan teliti), kerana tiada pautan kepadanya dalam halaman. Pembaikan: sediakan senarai URL untuk spider, atau terbitkan dokumen OpenAPI, atau tambah pautan ke halaman ujian.
</details>

</div>

---

## Makmal 5.5: Bandingkan dan padankan

**Tujuan.** Menggabungkan semua yang anda tahu.

Isi jadual ini bagi **sekurang-kurangnya lapan** kelemahan daripada threat model Modul 0:

| Kelemahan | Semgrep (Modul 2) | ZAP (modul ini) | Hanya manual |
|---|---|---|---|
| SQL injection log masuk | | | |
| XSS tersimpan (guestbook) | | | |
| Command injection | | | |
| Path traversal | | | |
| Cookie sesi boleh dipalsukan | | | |
| IDOR `/api/users/{id}` | | | |

<details>
<summary>Jawapan</summary>

<div class="trk trk-a" markdown="1">

| Kelemahan | Semgrep | ZAP | Hanya manual |
|---|---|---|---|
| SQL injection log masuk | ✔ (`p/gitlab`) | ✔ (pelan, bukan API) | |
| XSS tersimpan | ✘ | ✔ | |
| Command injection | ✔ | ✔ | |
| Path traversal | ✘ | ✔ (pelan) | |
| Cookie sesi boleh dipalsukan | ✘ | ✘ | ✔ |
| IDOR | ✘ | ✘ | ✔ |
| Deserialization tidak selamat | ✔ | ✘ | |

</div>

<div class="trk trk-b" markdown="1">

| Kelemahan | Semgrep | ZAP | Hanya manual |
|---|---|---|---|
| SQL injection log masuk | ✘ | ✔ | |
| XSS tersimpan | ✘ | ✔ | |
| Command injection | ✔ | ✔ | |
| Path traversal | ✘ | ✔ | |
| Cookie sesi boleh dipalsukan | ✘ | ✘ | ✔ |
| IDOR, mass assignment | ✘ | ✘ | ✔ |
| Open redirect | ✘ | ✘ (tidak dijumpai) | ✔ |
| Deserialization tidak selamat | ✔ | ✘ | |

</div>

Corak jelas: **kelemahan logik** (kebenaran, IDOR, cookie) hanya ditemui oleh manusia. SAST dan DAST saling melengkapi, dan kedua-duanya meninggalkan jurang yang menuntut ujian manual dan semakan reka bentuk (threat model). Jadual penuh dengan alat interaktif ada di [Modul 7](../modul-7-hardening/README.md#rumusan-alat-mana-menangkap-apa).
</details>

---

## Makmal 5.6: Baiki dan imbas semula

**Tujuan.** Menutup kelemahan DAST dan mengesahkan dengan imbasan.

Simpan tampalan DAST (bahagian **Fail modul**) dalam folder repo. Tampalan ini **mengandaikan tampalan SAST Modul 2 sudah diterapkan** (ia bina di atasnya). Jika anda menulis pembaikan sendiri, baca tampalan sebagai rujukan dan salin idea.

<div class="trk trk-a" markdown="1">

```bash
git apply --check aspnet-dast.patch && git apply aspnet-dast.patch
git diff --stat
```

Baca `git diff`. Pembaikan: **output encoding** (`WebUtility.HtmlEncode`) untuk XSS, **pengesahan laluan** (`GetFullPath` mesti bermula dengan folder `files`) untuk path traversal, **hanya redirect tempatan** untuk open redirect, **header keselamatan** (CSP, `X-Frame-Options`, `X-Content-Type-Options`, `Permissions-Policy`), CORS yang dihadkan, dan halaman pengecualian pembangunan hanya dalam mod Development.

</div>

<div class="trk trk-b" markdown="1">

```bash
git apply --check laravel-dast.patch && git apply laravel-dast.patch
git diff --stat
```

Baca `git diff`. Pembaikan: Blade **`{{ }}`** (dengan encoding) menggantikan `{!! !!}` untuk XSS, `basename()` untuk path traversal, **hanya redirect tempatan**, **token CSRF** dihidupkan semula (`@csrf` dalam borang, dan pengecualian hanya untuk `api/*`), middleware **header keselamatan**, dan bendera `HttpOnly` pada cookie sesi.

</div>

Bina semula, jalankan dan sahkan fungsi dahulu (ujian manual), kemudian imbas semula.

<div class="trk trk-a" markdown="1">

```bash
docker rm -f kedai 2>/dev/null
docker buildx build --provenance=false --sbom=false --load -t aspnet-app:dast aspnet-app
docker run -d --name kedai --network dast aspnet-app:dast
sleep 6
docker run --rm --network dast curlimages/curl -s "http://kedai:8080/search?q=%3Cb%3E" | grep -o "&lt;b&gt;"
docker run --rm --network dast curlimages/curl -s -o /dev/null -w "traversal: %{http_code}\n" "http://kedai:8080/download?file=../appsettings.json"
docker run --rm --network dast curlimages/curl -s -o /dev/null -w "redirect luar: %{http_code}\n" "http://kedai:8080/redirect?url=https://example.org"
```

</div>

<div class="trk trk-b" markdown="1">

```bash
docker rm -f kedai 2>/dev/null
docker buildx build --provenance=false --sbom=false --load -t laravel-app:dast laravel-app
docker run -d --name kedai --network dast laravel-app:dast
sleep 10
docker run --rm --network dast curlimages/curl -s "http://kedai:8080/search?q=%3Cb%3E" | grep -o "&lt;b&gt;"
docker run --rm --network dast curlimages/curl -s -o /dev/null -w "traversal: %{http_code}\n" "http://kedai:8080/download?file=../.env"
docker run --rm --network dast curlimages/curl -s -o /dev/null -w "POST tanpa token CSRF: %{http_code}\n" -X POST http://kedai:8080/guestbook -d name=a -d message=b
```

</div>

Jangkaan: `&lt;b&gt;` (tag dienkod), `traversal: 404`, `redirect luar: 400` (Trek A), `POST tanpa token CSRF: 419` (Trek B). Kemudian imbas semula:

```bash
rm -f zap-hasil/pelan.json
zap zap.sh -cmd -autorun /zap/wrk/zap-plan.yaml
python3 ringkas-zap.py zap-hasil/pelan.json
```

<details>
<summary>Jawapan: apa yang kekal?</summary>

<div class="trk trk-a" markdown="1">

Isyarat jatuh daripada **18** kepada **7**, dan **tiada lagi isyarat Tinggi**. Yang kekal: **Absence of Anti-CSRF Tokens** (Sederhana; tampalan ini tidak menambah perlindungan CSRF, itu kerja tambahan anda), amaran CSP tentang arahan tanpa *fallback*, dan beberapa Maklumat/Rendah.
</div>

<div class="trk trk-b" markdown="1">

Isyarat jatuh daripada **17** kepada **8**, dan **tiada lagi isyarat Tinggi atau anti-CSRF**. Yang kekal: amaran CSP tentang arahan tanpa *fallback*, cookie `Laravel` sendiri tanpa `HttpOnly`, dan `X-Powered-By` yang didedahkan oleh pelayan PHP terbina dalam.
</div>

Ingat: pelan aktif menyerang apa yang ia jumpa. Kelemahan logik (cookie palsu, IDOR) **masih ada** kerana ia tidak ditampal dan tidak pernah dikesan.
</details>

Hentikan: `docker rm -f kedai`.

---

## Makmal 5.7: Quality gate DAST

**Tujuan.** Menjadikan baseline sebagai pintu dalam CI.

ZAP memulangkan exit code: `0` lulus, `1` ada **FAIL**, `2` ada **WARN** tanpa FAIL, `3` ralat. Secara lalai kebanyakan isyarat ialah WARN. Tanpa `-I`, baseline memberi `2` bila ada amaran:

```bash
zap zap-baseline.py -t http://kedai:8080 -m 1 > /dev/null; echo "exit=$?"
```

Untuk menggagalkan pipeline bagi peraturan tertentu, jadikan ia **FAIL** melalui fail konfigurasi (format: ID peraturan, tindakan, komen, dipisahkan tab). Letak dalam `zap-hasil/`:

```bash
printf "10020\tFAIL\t(Anti-clickjacking)\n10038\tFAIL\t(CSP tiada)\n" > zap-hasil/zap-baseline.conf
zap zap-baseline.py -t http://kedai:8080 -c zap-baseline.conf -m 1 > /dev/null; echo "exit=$?"
```

Jawapan jangkaan: `exit=2` pada arahan pertama, `exit=1` pada yang kedua (apabila app belum ditampal). Selepas tampalan Makmal 5.6, peraturan-peraturan itu lulus kerana header sudah ada.

Pendekatan yang praktikal: mulakan dengan beberapa peraturan penting sebagai FAIL, kekalkan selebihnya sebagai WARN, dan **ketatkan** dari masa ke masa. Menetapkan semua sebagai FAIL pada hari pertama hanya menjadikan pasukan mengabaikan pipeline.

## Senarai semak Modul 5

- [ ] Saya menjalankan baseline, imbasan aktif (pelan) dan (Trek A) imbasan API, dan tahu apa yang setiap satu temui
- [ ] Saya faham kenapa `zap-full-scan` tidak digunakan pada laptop 8 GB, dan apa yang dilakukan pelan
- [ ] Saya menyenaraikan kelemahan yang SAST temui, DAST temui, dan hanya ujian manual temui
- [ ] Saya menerapkan tampalan DAST, mengesahkan fungsi, dan imbasan semula tiada isyarat Tinggi
- [ ] Saya boleh menggagalkan pipeline melalui exit code dan fail konfigurasi ZAP
- [ ] Saya faham bahawa DAST hanya menguji apa yang ia jumpa

## Rujukan

- ZAP (dahulu OWASP ZAP): <https://www.zaproxy.org/docs/>
- ZAP Automation Framework: <https://www.zaproxy.org/docs/automate/automation-framework/>
- OWASP Top 10: <https://owasp.org/Top10/>
