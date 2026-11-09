# Modul 2: SAST dan kod yang dijana AI

**Hari 2, 9:00 pagi hingga 1:00 petang**

Dalam modul ini anda akan:

1. Faham apa SAST boleh dan tidak boleh lakukan, dan kenapa hasilnya bergantung pada **set peraturan**.
2. Menjalankan **Semgrep** pada app anda, membandingkan set peraturan dan membuat **triaj** (benar atau positif palsu).
3. Mengenal pasti kelemahan yang SAST **terlepas**, dan memadankannya dengan threat model anda.
4. Membaiki SQL injection, command injection dan deserialization, kemudian mengesahkan pembaikan dengan ujian fungsi **dan** imbasan semula.
5. Mengimbas kod yang dijana AI dan mengaplikasikan **quality gate** serta pengurusan temuan.
6. Menjalankan Semgrep sebagai pintu dalam **GitLab CI** dan membaca keputusannya.

> Prasyarat: [Modul 1](../modul-1-secret/README.md) siap. Fungsi `semgrep` dalam `alat.sh` berfungsi. App anda berjalan seperti dalam [Modul 0](../modul-0-pengenalan/README.md#makmal-0-2-jalankan-app-lab). Untuk Makmal 2.8, repo anda sudah dihantar ke GitLab (Persediaan 4d).

## Jadual

| Masa | Aktiviti |
|---|---|
| 9:00 – 9:40 | Teori: SAST, taint analysis, set peraturan, positif palsu |
| 9:40 – 10:40 | Makmal 2.1 hingga 2.3: imbas, bandingkan, triaj |
| 10:40 – 10:55 | Rehat |
| 10:55 – 11:35 | Makmal 2.4 dan 2.5: yang terlepas, baiki dan sahkan |
| 11:35 – 12:30 | Makmal 2.6: kod yang dijana AI |
| 12:30 – 12:45 | Makmal 2.7: quality gate dan semakan |
| 12:45 – 1:00 | Makmal 2.8: SAST dalam GitLab CI |

---

## Teori ringkas

### Apa itu SAST

**SAST** (Static Application Security Testing) membaca kod sumber **tanpa menjalankannya** dan mencari corak yang tidak selamat. Ia pantas, boleh dijalankan pada setiap commit, dan menunjuk kepada **baris kod** sebenar.

| Teknik | Cara | Contoh |
|---|---|---|
| Padanan corak | Cari bentuk kod tertentu | `"SELECT ... " + input` |
| Taint analysis | Jejak data daripada **sumber** (input pengguna) ke **sink** (SQL, shell) | `$_GET['id']` sampai ke `$db->query(...)` |
| Analisis aliran data lebih dalam | Merentas fail dan fungsi | Biasanya dalam edisi komersial |

### Apa SAST tidak boleh lakukan

- Ia tidak melihat app yang **berjalan**: konfigurasi, header, cara pelayan menjawab.
- Ia lemah pada **logik perniagaan**: cookie yang boleh dipalsukan, IDOR, kebenaran yang tiada.
- Hasilnya ada **positif palsu** (amaran yang bukan masalah) dan **negatif palsu** (masalah sebenar yang tidak dilihat).
- Hasilnya bergantung pada **peraturan** yang anda muatkan, dan pada **bentuk kod**.

Dalam makmal ini anda akan melihat ketiga-tiganya dengan data sebenar.

### Semgrep

**Semgrep** menulis peraturan dalam bentuk yang kelihatan seperti kod itu sendiri, dan mempunyai pustaka peraturan komuniti (`p/default`, `p/owasp-top-ten`, `p/gitlab` dan lain-lain). Ia menyokong C#, PHP dan banyak bahasa lain dalam satu alat. Untuk .NET dan Laravel, alat khusus bahasa wujud sebagai pelengkap: penganalisis Roslyn (`Microsoft.CodeAnalysis.NetAnalyzers`, Security Code Scan) dan PHPStan/Larastan. Bengkel ini menumpu pada Semgrep supaya kedua-dua trek mempunyai alat yang sama.

### Semgrep lawan SonarQube

Banyak organisasi sudah menggunakan **SonarQube**, jadi anda mungkin bertanya kenapa ia tidak ada dalam bengkel ini. Kedua-duanya ialah alat analisis statik, tetapi dibina untuk tujuan yang berbeza:

| | Semgrep (dalam bengkel) | SonarQube Community Build |
|---|---|---|
| **Cara berjalan** | Kontena sekali guna, tiada pelayan | Pelayan berterusan: tiga proses Java (termasuk Elasticsearch) dan pangkalan data, ditambah pengimbas (*scanner*) pada CI |
| **Sumber** | Ringan | Dokumentasi rasmi: 4 GB RAM, 2 teras dan 30 GB cakera bagi pemasangan kecil (sehingga satu juta baris kod) |
| **Fokus** | Keselamatan; peraturan sendiri mudah ditulis | Kualiti kod (bug, *code smell*, pertindihan, liputan ujian) dan keselamatan |
| **Keputusan** | Log CI dan SARIF | Papan pemuka web, sejarah trend dan quality gate terbina dalam |
| **C# dan PHP** | Disokong | Disokong |
| **Cawangan dan merge request** | Mengimbas apa yang ada dalam checkout | Analisis cawangan dan *pull/merge request* hanya dalam edisi berbayar (Developer dan ke atas) |
| **Taint analysis merentas fungsi dan fail** | Tidak dibincangkan dalam bengkel ini | Edisi berbayar (Developer dan ke atas) |

**Kenapa tidak dalam bengkel ini.** SonarQube bertindih dengan Semgrep untuk matlamat kita (SAST sebagai pintu CI), dan pelayannya menambah beban pada server lab yang sudah menjalankan Harbor dan GitLab. Menambahnya juga bermakna peserta mempelajari satu lagi alat sebelum sempat memahami konsepnya.

**Bila yang mana.** Semgrep sesuai untuk pintu keselamatan yang ringan, peraturan khusus projek, dan CI yang pantas. SonarQube sesuai jika pasukan mahu papan pemuka, trend kualiti dan liputan ujian dalam satu tempat. Banyak pasukan menggunakan kedua-duanya.

**Apa yang anda pelajari tetap terpakai.** Konsep yang sama berpindah terus ke SonarQube: peraturan, triaj temuan, positif palsu, menerima temuan dengan alasan, dan **quality gate** yang menggagalkan CI. Hanya alatnya berbeza.

> Maklumat keperluan dan edisi diambil daripada dokumentasi SonarSource (disemak pada 9 November 2026). Ia berubah mengikut versi, jadi semak dokumentasi semasa sebelum membuat keputusan.

---

## Makmal 2.1: Imbas app anda

**Tujuan.** Jalankan Semgrep dan catat apa yang dilihat.

<div class="trk trk-a" markdown="1">

```bash
source alat.sh
semgrep scan --quiet --config p/default --config p/gitlab aspnet-app
```

</div>

<div class="trk trk-b" markdown="1">

```bash
source alat.sh
semgrep scan --quiet --config p/default --config p/phpcs-security-audit laravel-app
```

</div>

Muat turun peraturan memerlukan rangkaian; imbasan pertama mengambil beberapa saat lebih lama. Hasil dipaparkan sebagai blok dengan **fail, baris, peraturan, keterukan**.

Catat dalam jadual: fail, baris, nama peraturan, dan pada fikiran anda sama ada ia **benar** atau **positif palsu**. Jumlah temuan: **7** untuk kedua-dua trek.

---

## Makmal 2.2: Bandingkan set peraturan

**Tujuan.** Lihat bahawa jawapan "berapa banyak kelemahan?" bergantung pada peraturan yang dimuatkan.

<div class="trk trk-a" markdown="1">

```bash
for s in p/csharp p/owasp-top-ten p/default p/gitlab p/security-audit p/secrets; do
  printf "%-22s" "$s"
  semgrep scan --quiet --config "$s" --json aspnet-app | python3 -c "import sys,json; print(len(json.load(sys.stdin)['results']))"
done
```

</div>

<div class="trk trk-b" markdown="1">

```bash
for s in p/php p/owasp-top-ten p/default p/gitlab p/security-audit p/phpcs-security-audit p/secrets; do
  printf "%-26s" "$s"
  semgrep scan --quiet --config "$s" --json laravel-app | python3 -c "import sys,json; print(len(json.load(sys.stdin)['results']))"
done
```

</div>

<details>
<summary>Jawapan jangkaan</summary>

<div class="trk trk-a" markdown="1">

| Set | Temuan |
|---|---|
| `p/csharp` | 1 |
| `p/owasp-top-ten` | 2 |
| `p/default` | 3 |
| `p/gitlab` | **4** |
| `p/security-audit` | 0 |
| `p/secrets` | 0 |

`p/gitlab` menangkap SQL injection dan command injection; `p/default` menangkap deserialization. Gabungan kedua-duanya memberi 7.
</div>

<div class="trk trk-b" markdown="1">

| Set | Temuan |
|---|---|
| `p/php` | 0 |
| `p/owasp-top-ten` | 2 |
| `p/default` | 4 |
| `p/gitlab` | 0 |
| `p/security-audit` | 0 |
| `p/phpcs-security-audit` | 4 |
| `p/secrets` | 0 |

Set yang sama yang berguna untuk .NET (`p/gitlab`) memberi **0** pada Laravel. Gabungan `p/default` dan `p/phpcs-security-audit` memberi 7.
</div>

Pengajaran: pilih set peraturan mengikut **bahasa dan framework**, dan jangan anggap satu set sahaja cukup. Hasil boleh berubah apabila peraturan dikemas kini; kunci versi dalam CI.
</details>

---

## Makmal 2.3: Triaj

**Tujuan.** Menentukan setiap temuan sebagai **benar**, **positif palsu**, atau **bunyi** (benar tetapi tidak relevan).

Untuk setiap temuan dari Makmal 2.1, buka fail pada baris itu dan baca kod. Tanya:

1. Adakah data daripada pengguna sampai ke baris ini?
2. Adakah ada kawalan yang menghalang kesannya?
3. Jika ia benar, apa kesannya (rujuk threat model Modul 0)?

<details>
<summary>Jawapan</summary>

<div class="trk trk-a" markdown="1">

| Fail dan baris | Peraturan | Keputusan |
|---|---|---|
| `Program.cs` L50 (`/search`) | SCS0002 | **Benar**: SQL digabung dengan `q` |
| `Program.cs` L131 (`/login`) | SCS0002 | **Benar** |
| `Program.cs` L231 (`Db.Exec`) | SCS0002 | **Positif palsu**: SQL benih data tetap, tiada input pengguna |
| `Program.cs` L102 (`/ping`) | SCS0001 | **Benar**: arahan shell digabung dengan `host` |
| `Program.cs` L204 (`/api/import`) | insecure-newtonsoft-deserialization | **Benar** |
| `Program.cs` L17 | stacktrace-disclosure | **Benar**: halaman pengecualian pembangunan aktif |
| `Dockerfile` L15 | missing-user-entrypoint | **Benar**: bejana berjalan sebagai root |

</div>

<div class="trk trk-b" markdown="1">

| Fail dan baris | Peraturan | Keputusan |
|---|---|---|
| `routes/web.php` L41 (`/ping`) | exec-use | **Benar**: `shell_exec` dengan `host` |
| `routes/web.php` L94 (`/api/import`) | unserialize-use | **Benar** |
| `routes/web.php` L61 dan `DatabaseSeeder.php` L24, L25 | weak-crypto | **Benar**: MD5 untuk kata laluan |
| `Dockerfile` L17 | missing-user | **Benar**: bejana berjalan sebagai root |
| `.npmrc` L1 | npm-missing-minimum-release-age | **Bunyi**: tidak berkaitan dengan lab (rangka Laravel menyertakan konfigurasi npm) |

</div>
</details>

---

## Makmal 2.4: Apa yang terlepas

**Tujuan.** Sedar bahawa "tiada temuan" bukan bermakna "selamat".

Rujuk senarai kelemahan dalam threat model Modul 0 dan jadual Makmal 0.3. Dari temuan Semgrep, kelemahan mana yang **anda tahu wujud tetapi tiada temuan**?

Cuba cari sendiri dalam kod:

<div class="trk trk-a" markdown="1">

```bash
grep -n "MapGet\|MapPost" aspnet-app/Program.cs
```

Baca titik akhir `/search`, `/guestbook`, `/download`, `/redirect`, `/admin` dan `/api/users/{id}`.

</div>

<div class="trk trk-b" markdown="1">

```bash
cat laravel-app/routes/web.php
```

Baca laluan `/search`, `/guestbook`, `/download`, `/redirect`, `/admin`, `/api/users/{id}` dan `/api/profile/{id}`.

</div>

<details>
<summary>Jawapan</summary>

Kelemahan berikut **tiada temuan** daripada set yang diuji:

| Kelemahan | Kenapa terlepas |
|---|---|
| XSS (pantulan dan tersimpan) | Output HTML dibina daripada rentetan; tiada peraturan menandainya dalam konteks ini |
| Path traversal | Gabungan laluan dengan input tidak ditanda |
| Open redirect | Tidak ditanda |
| Cookie sesi boleh dipalsukan, IDOR | Kelemahan **logik**, bukan corak |
| Mass assignment (Laravel) | Konfigurasi model, bukan corak fungsi |
| Trek A: MD5, CORS terlalu longgar | Tiada peraturan dalam set yang diuji |
| Trek B: SQL injection | Peraturan taint tidak mengesannya dalam bentuk kod ini (lihat di bawah) |

Dua kategori ini yang DAST (Modul 5) dan ujian manual akan tutup. Itulah sebab satu alat tidak mencukupi.
</details>

---

## Makmal 2.5: Baiki dan sahkan

**Tujuan.** Membaiki kelemahan yang SAST nampak, dan **mengesahkan** pembaikan itu dengan dua cara.

Cuba baiki sendiri dahulu (selama 15 minit): SQL injection pada `/search` dan `/login`, command injection pada `/ping`, dan deserialization pada `/api/import`. Panduan:

- SQL: gunakan **query berparameter**, jangan gabung rentetan.
- Command injection: elak shell; hantar hujah sebagai senarai; sahkan input dengan senarai putih aksara.
- Deserialization: jangan benarkan jenis sewenang-wenangnya.

Kemudian bandingkan dengan tampalan rujukan. Jika anda sudah mengubah `Program.cs` (Trek A) atau `routes/web.php` (Trek B), simpan kerja anda dalam cawangan lain dahulu (`git switch -c kerja-sendiri && git commit -am "kerja sendiri" && git switch -`). Simpan fail tampalan dari bahagian **Fail modul** dalam folder repo, kemudian:

<div class="trk trk-a" markdown="1">

```bash
git apply --check aspnet-sast.patch && git apply aspnet-sast.patch
git diff --stat
```

</div>

<div class="trk trk-b" markdown="1">

```bash
git apply --check laravel-sast.patch && git apply laravel-sast.patch
git diff --stat
```

</div>

Lihat perubahan dengan `git diff`.

### Pengesahan 1: ujian fungsi

Bina semula dan jalankan app, kemudian cuba serangan Modul 0 sekali lagi.

<div class="trk trk-a" markdown="1">

```bash
docker rm -f kedai 2>/dev/null
docker buildx build --provenance=false --sbom=false --load -t aspnet-app:baiki aspnet-app
docker run -d --name kedai -p 8080:8080 aspnet-app:baiki
sleep 5
APP=http://localhost:8080
curl -s "$APP/search?q=laptop" | grep -oE "<td>Laptop[^<]*"
curl -s -X POST $APP/login --data-urlencode "username=admin'--" --data-urlencode "password=x" | grep -oE "Log masuk gagal|Selamat datang[^<]*"
curl -s -w " [%{http_code}]\n" "$APP/ping?host=127.0.0.1;id"
```

</div>

<div class="trk trk-b" markdown="1">

```bash
docker rm -f kedai 2>/dev/null
docker buildx build --provenance=false --sbom=false --load -t laravel-app:baiki laravel-app
docker run -d --name kedai -p 8081:8080 laravel-app:baiki
sleep 8
APP=http://localhost:8081
curl -s "$APP/search?q=laptop" | grep -oE "<td>Laptop[^<]*"
curl -s -X POST $APP/login --data-urlencode "username=admin'--" --data-urlencode "password=x" | grep -oE "Log masuk gagal|Selamat datang[^<]*"
curl -s -o /dev/null -w "%{http_code}\n" "$APP/ping?host=127.0.0.1;id"
```

</div>

Carian biasa masih berfungsi, suntikan SQL kini memberi `Log masuk gagal`, dan `;id` ditolak dengan kod `400`. Hentikan app: `docker rm -f kedai`.

### Pengesahan 2: imbasan semula

<div class="trk trk-a" markdown="1">

```bash
semgrep scan --quiet --config p/default --config p/gitlab aspnet-app
```

</div>

<div class="trk trk-b" markdown="1">

```bash
semgrep scan --quiet --config p/default --config p/phpcs-security-audit laravel-app
```

</div>

<details>
<summary>Jawapan: apa yang berubah dalam imbasan?</summary>

<div class="trk trk-a" markdown="1">

Temuan turun daripada **7** kepada **4**. Tiga yang hilang ialah SQL injection (dua) dan deserialization. Dua temuan yang kekal berkaitan SQL/shell ialah:

- SCS0002 pada `Db.Exec`: positif palsu yang sama seperti sebelum ini.
- SCS0001 pada `Process.Start`: kod kini selamat (tiada shell, hujah senarai, input disahkan), tetapi peraturan masih menanda **penggunaan** `Process.Start`. Ini temuan yang perlu **diterima dengan alasan** (lihat Makmal 2.7) bukannya dibiarkan.

Baki lain ialah `stacktrace-disclosure` dan `missing-user-entrypoint`, yang bukan sebahagian daripada tampalan ini.
</div>

<div class="trk trk-b" markdown="1">

Bilangan temuan kekal **7**. Ini mengejutkan tetapi penting: Semgrep **tidak pernah** melihat SQL injection dalam kod Laravel ini, jadi membaikinya tidak mengubah bilangan. Temuan yang kekal ialah `exec-use` (penggunaan `shell_exec`, walaupun kini dengan `escapeshellarg`), `unserialize-use` (walaupun kini dengan `allowed_classes => false`), MD5, `Dockerfile` dan `.npmrc`.

Pengajaran: **ujian fungsi** (carian dan log masuk) ialah satu-satunya bukti bahawa SQL injection sudah ditutup. Jangan menyamakan "tiada temuan" dengan "selamat" dan "bilangan temuan sama" dengan "tiada kemajuan".
</div>
</details>

---

## Makmal 2.6: Kod yang dijana AI

**Tujuan.** Menyemak kod yang kelihatan baik tetapi tidak selamat, dan memahami kenapa kelajuan menulis tidak menambah kelajuan menyemak.

Simpan `contoh-ai.cs` dan `contoh-ai.php` (bahagian **Fail modul**) dalam satu folder `contoh-ai/`. Fail itu mewakili jawapan asisten AI kepada permintaan "tulis kelas log masuk dan muat turun fail". Baca dahulu dan senaraikan kelemahan yang anda nampak (5 minit), kemudian imbas:

<div class="trk trk-a" markdown="1">

```bash
semgrep scan --quiet --config p/default --config p/gitlab contoh-ai/contoh-ai.cs
```

</div>

<div class="trk trk-b" markdown="1">

```bash
for s in p/default p/php p/phpcs-security-audit; do
  echo "## $s"; semgrep scan --quiet --config $s contoh-ai/contoh-ai.php | grep -E "❯|php" | head -12
done
```

</div>

Soalan:

1. Berapa kelemahan yang anda tulis? Berapa yang ditangkap Semgrep?
2. Kenapa Semgrep menangkap SQL injection di sini, sedangkan pada app lab Trek B ia **tidak** menangkapnya sama sekali?
3. Siapa yang bertanggungjawab ke atas kod ini jika ia sampai ke produksi?

<details>
<summary>Jawapan</summary>

<div class="trk trk-a" markdown="1">

Kelemahan dalam `contoh-ai.cs`: SQL injection, kata laluan ditanam dalam kod, MD5, pengesahan sijil TLS dimatikan, dan path traversal. Semgrep (set di atas) menangkap **hanya SQL injection**. Yang lain perlu: Gitleaks (kata laluan), peraturan tambahan (MD5, TLS), dan semakan manusia (path traversal).

</div>

<div class="trk trk-b" markdown="1">

Kelemahan dalam `contoh-ai.php`: SQL injection, `include` daripada input (LFI/RFI), MD5, `unserialize` daripada cookie, command injection, XSS dan kata laluan DB ditanam. Hasil mengikut set: `p/default` menangkap SQL injection, `unserialize` dan `exec`; `p/php` menangkap SQL injection, exec dan XSS; `p/phpcs-security-audit` menangkap `include`, MD5 dan exec. **Tiada satu set** menangkap kesemuanya, dan kata laluan DB perlu Gitleaks.

</div>

Perbezaan antara kod ini dan `Program.cs`: di sini input masuk melalui sumber yang jelas (`$_GET`, parameter kaedah) terus ke sink dalam fungsi yang sama, jadi taint analysis berjaya. Dalam app lab, input datang melalui lambda dan helper, jadi sebahagian peraturan terlepas. Bentuk kod mempengaruhi apa yang dilihat.

Pemilik kod ialah **anda**, bukan asisten AI. Imbasan automatik ialah jaring keselamatan, bukan pengganti semakan.
</details>

Cabaran: minta asisten AI yang anda gunakan (jika ada) membaiki kod itu, kemudian **imbas jawapannya** dengan alat yang sama. Adakah semua isu hilang? Adakah ada isu baharu?

---

## Makmal 2.7: Quality gate dan pengurusan temuan

**Tujuan.** Menjadikan imbasan sebagai pintu dalam pipeline, dan mengurus temuan yang diterima.

**Pintu berasaskan exit code.** Semgrep memulangkan `0` walaupun ada temuan, kecuali anda minta ia gagal:

<div class="trk trk-a" markdown="1">

```bash
semgrep scan --quiet --config p/default --config p/gitlab --severity ERROR --error aspnet-app > /dev/null; echo "exit=$?"
```

</div>

<div class="trk trk-b" markdown="1">

```bash
semgrep scan --quiet --config p/default --config p/phpcs-security-audit --severity ERROR --error laravel-app > /dev/null; echo "exit=$?"
```

</div>

`exit=1` bermakna ada temuan keterukan ERROR. Di CI, ini yang menggagalkan job. `--severity ERROR` menjadikan WARNING tidak menggagalkan, jadi pasukan boleh mula dengan pintu yang longgar dan ketatkan kemudian.

**SARIF.** Format piawai untuk memaparkan temuan dalam GitHub Code Scanning:

```bash
semgrep scan --quiet --config p/default --sarif -o hasil.sarif .
```

**Menerima temuan dengan alasan.** Jika temuan itu positif palsu atau diterima, tandakan dengan komen `nosemgrep` di baris sebelumnya, **dengan nama peraturan dan alasan**:

<div class="trk trk-a" markdown="1">

```csharp
// nosemgrep: gitlab.security_code_scan.SCS0002-1 -- SQL benih data tetap, tiada input pengguna
using var cmd = new SqliteCommand(sql, conn);
```

Letakkan komen itu di atas baris `using var cmd = new SqliteCommand(sql, conn);` dalam `Db.Exec`, kemudian imbas semula: positif palsu itu hilang daripada hasil.

</div>

<div class="trk trk-b" markdown="1">

```php
// nosemgrep: php.lang.security.exec-use.exec-use -- hos disahkan dengan regex dan escapeshellarg
$output = shell_exec('ping -c 1 ' . escapeshellarg($host) . ' 2>&1');
```

Letakkan komen sebelum baris yang berkenaan, kemudian imbas semula.

</div>

Peraturan: setiap pengecualian perlu ada **alasan** dan, dalam projek sebenar, **tarikh semakan semula**. Pengecualian tanpa alasan ialah hutang keselamatan yang tersembunyi.

---

## Makmal 2.8: SAST dalam GitLab CI

**Tujuan.** Melihat Semgrep berjalan sebagai pintu dalam GitLab CI pada setiap `git push`, dan membaca keputusannya.

<div class="ci ci-gh" markdown="1">

Makmal ini menggunakan GitLab CI. Jika anda memilih GitHub Actions, langkau ke [Modul 6](../modul-6-cicd/README.md), yang menunjukkan job SAST yang sama dalam workflow GitHub.

</div>

<div class="ci ci-gl" markdown="1">

Setakat ini anda menjalankan Semgrep sendiri di laptop. Di sini kita menjalankan arahan yang **sama** (dengan `--severity ERROR --error` daripada Makmal 2.7) di server, supaya tiada commit boleh melepasinya tanpa disemak. Prasyarat: repo anda sudah dihantar ke GitLab (Persediaan 4d), dan perubahan Makmal 2.5 dan 2.7 sudah disimpan dalam folder repo.

**Langkah 1: cipta fail pipeline.** Dari akar repo:

<div class="trk trk-a" markdown="1">

```bash
cat > .gitlab-ci.yml <<'EOF'
stages: [imbas]

sast:
  stage: imbas
  image: { name: "semgrep/semgrep:1.183.0", entrypoint: [""] }
  variables:
    APP_DIR: aspnet-app
    SEMGREP_SEND_METRICS: "off"
  script:
    - semgrep scan --quiet --config p/default --config p/gitlab --config p/phpcs-security-audit --severity ERROR --error --exclude Dockerfile "$APP_DIR"
EOF
```

</div>

<div class="trk trk-b" markdown="1">

```bash
cat > .gitlab-ci.yml <<'EOF'
stages: [imbas]

sast:
  stage: imbas
  image: { name: "semgrep/semgrep:1.183.0", entrypoint: [""] }
  variables:
    APP_DIR: laravel-app
    SEMGREP_SEND_METRICS: "off"
  script:
    - semgrep scan --quiet --config p/default --config p/gitlab --config p/phpcs-security-audit --severity ERROR --error --exclude Dockerfile "$APP_DIR"
EOF
```

</div>

Perhatikan:

- `image` ialah Semgrep yang sama (v1.183.0) seperti dalam `alat.sh`, jadi keputusan di server dan di laptop sepatutnya sama.
- `--severity ERROR --error` menjadikan temuan ERROR menggagalkan job (`exit=1`), seperti dalam Makmal 2.7.
- `--exclude Dockerfile` mengecualikan sementara temuan `missing-user` pada Dockerfile. Ia dibaiki dalam Modul 4, dan Modul 6 membuang pengecualian ini.
- Job ini ialah job `sast` yang sama dalam pipeline penuh Modul 6.

**Langkah 2: tolak.** Semak dahulu apa yang akan dihantar, kemudian tolak ke GitLab:

```bash
git status --short
git add -A
git commit -m "Tambah SAST dalam GitLab CI"
git push gitlab main
```

`git status --short` hanya patut menunjukkan fail kod, tampalan dan `.gitlab-ci.yml`. Jika ada fail rahsia (contohnya `rahsia-ujian.txt`, `.env` atau `cosign.key`), jangan `git add` fail itu: lihat bahagian `.gitignore` dalam Modul 1.

**Langkah 3: lihat pipeline.** Buka `https://gitlab.lab.test:8929/pesertaNN/devsecops-lab/-/pipelines`, klik pipeline paling atas, kemudian job `sast` untuk melihat log. Status `pending` bermakna job menunggu giliran: runner dikongsi dan hanya menjalankan tiga job serentak, jadi dengan ramai peserta ia boleh mengambil masa beberapa minit. **Tunggu, jangan tolak berulang kali.** Pipeline pertama juga lebih lambat kerana runner memuat turun imej Semgrep.

<div class="trk trk-a" markdown="1">

Pipeline mesti **gagal** (`failed`). Log berakhir dengan `ERROR: Job failed: exit code 1`, dan di atasnya anda melihat satu temuan **Blocking**: `gitlab.security_code_scan.SCS0001-1` pada `Process.Start` dalam `Program.cs`. Kod itu sudah selamat (tiada shell, hujah dihantar sebagai senarai, hos disahkan), tetapi peraturan menanda **penggunaan** `Process.Start`. Jika anda belum menerima `SCS0002` dalam Makmal 2.7, anda akan melihat dua temuan.

**Langkah 4: triaj dalam CI.** Ini ialah temuan yang diterima dengan alasan. Letakkan komen di baris sebelum kod yang ditanda dalam `aspnet-app/Program.cs`:

```csharp
// nosemgrep: gitlab.security_code_scan.SCS0001-1 -- hos disahkan dengan regex, hujah dihantar sebagai senarai
using var p = Process.Start(psi)!;
```

Kemudian:

```bash
git commit -am "Terima SCS0001 dengan alasan"
git push gitlab main
```

Pipeline kali ini mesti **lulus** (`passed`, tanda hijau).

</div>

<div class="trk trk-b" markdown="1">

Pipeline mesti **gagal** (`failed`). Log berakhir dengan `ERROR: Job failed: exit code 1`, dan di atasnya anda melihat **tiga temuan `weak-crypto`**: MD5 pada `DatabaseSeeder.php` (dua) dan `routes/web.php` (satu). Jika anda belum menerima `exec-use` dalam Makmal 2.7, anda akan melihat empat.

MD5 untuk kata laluan ialah kelemahan **sebenar**, jadi jangan tutup dengan `nosemgrep`. Ia dibaiki dalam Modul 6 dengan tampalan bcrypt. Untuk sekarang pipeline kekal merah, dan itulah tugas pintu: tiada kod dengan kelemahan sebenar boleh melepasinya.

</div>

**Apa yang anda pelajari:**

- Pintu berjalan **sendiri** pada setiap push. Anda tidak perlu ingat untuk menjalankannya.
- Keputusan ditentukan oleh **exit code**, dan log menunjukkan fail, baris dan peraturan yang menyebabkan kegagalan.
- Temuan yang diterima mesti ada **alasan** dalam kod, seperti dalam Makmal 2.7, dan temuan sebenar mesti **dibaiki**, bukan dipadamkan.
- Pipeline penuh dalam Modul 6 menambah Gitleaks, SCA, IaC dan binaan imej di sekeliling job yang sama.

</div>

## Senarai semak Modul 2

- [ ] Saya menjalankan Semgrep dan mencatat 7 temuan dengan keterukan masing-masing
- [ ] Saya membandingkan set peraturan dan tahu kenapa bilangannya berbeza
- [ ] Saya mengklasifikasikan setiap temuan (benar, positif palsu, bunyi)
- [ ] Saya menyenaraikan kelemahan yang SAST terlepas dan tahu alat mana yang akan menangkapnya
- [ ] Saya membaiki SQL/command injection dan mengesahkan dengan ujian fungsi **dan** imbasan semula
- [ ] Saya mengimbas kod yang dijana AI dan menerangkan kenapa saya bertanggungjawab ke atasnya
- [ ] Saya boleh menjadikan Semgrep pintu dalam pipeline dengan `--error` dan menerima temuan dengan `nosemgrep` beralasan
- [ ] Saya melihat job `sast` berjalan dalam GitLab CI, gagal pada temuan ERROR, dan (Trek A) lulus selepas triaj beralasan

## Rujukan

- Semgrep: <https://semgrep.dev/docs/>
- OWASP Cheat Sheet: SQL Injection Prevention: <https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html>
- OWASP Cheat Sheet: OS Command Injection Defense: <https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html>
