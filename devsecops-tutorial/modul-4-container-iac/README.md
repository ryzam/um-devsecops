# Modul 4: Container, Harbor dan IaC

**Hari 3, 9:00 pagi hingga 1:00 petang**

Dalam modul ini anda akan:

1. Mengimbas imej kontena dan memahami dari mana kerentanan datang (OS, runtime, pakej app).
2. Mengimbas **Dockerfile** dengan tiga alat dan membandingkan apa yang setiap satu tegur.
3. Membina semula imej dengan Dockerfile yang **lebih selamat** (multi-stage, bukan root, tiada secret) dan mengukur perbezaannya.
4. Menolak imej ke **Harbor**, melihat imbasan automatik, dan menguji polisi yang menyekat imej berisiko, termasuk cara menerima risiko dengan **allowlist CVE**.
5. Mengimbas **K8s dan Terraform** (IaC) dan membaiki Terraform.

> Prasyarat: [Persediaan](../00-persediaan/README.md) bahagian Harbor siap (`docker login harbor.lab.test` berjaya), dan modul 1 hingga 3 siap. Imej `aspnet-app:latest` atau `laravel-app:latest` daripada [Modul 0](../modul-0-pengenalan/README.md) wujud.

## Jadual

| Masa | Aktiviti |
|---|---|
| 9:00 – 9:40 | Teori: lapisan imej, pilihan imej asas, Harbor |
| 9:40 – 10:25 | Makmal 4.1 dan 4.2: imbas imej dan Dockerfile |
| 10:25 – 10:40 | Rehat |
| 10:40 – 11:30 | Makmal 4.3: binaan selamat |
| 11:30 – 12:20 | Makmal 4.4: Harbor |
| 12:20 – 1:00 | Makmal 4.5 dan 4.6: IaC dan robot account |

---

## Teori ringkas

### Dari mana kerentanan dalam imej datang

Satu imej ialah timbunan lapisan. Setiap lapisan membawa pakej:

1. **Imej asas** (Ubuntu, Debian, Alpine): pakej OS seperti `apt`, `libc`, `openssl`.
2. **Runtime** (.NET, PHP): perpustakaan runtime itu sendiri.
3. **Pakej app**: dependency anda (SCA, Modul 3).
4. **Apa yang anda tambah**: alat binaan, `curl`, `git`, `composer`.

Setiap pakej yang tidak perlu semasa app berjalan hanya menambah **permukaan serangan** dan **bunyi** dalam imbasan.

### Amalan imej yang lebih selamat

| Amalan | Kenapa |
|---|---|
| **Multi-stage build** | Alat binaan (SDK, composer, git) kekal dalam peringkat binaan, bukan imej akhir |
| **Imej asas yang kecil dan sesuai** (`aspnet` bukan `sdk`; Alpine) | Lebih sedikit pakej, lebih sedikit kerentanan |
| **Bukan root** (`USER`) | Jika app dieksploit, penyerang tidak mendapat root dalam kontena |
| **Tiada secret dalam imej** | Imej disimpan dan dikongsi; secret dalam lapisan kekal selamanya |
| **`HEALTHCHECK`** | Orkestra tahu bila app tidak sihat |
| **Kemas kini pakej OS** semasa binaan | Menutup kerentanan yang sudah ada pembaikan |
| **Kunci versi imej asas** (tag tepat atau digest) | Binaan boleh diulang; tiada perubahan senyap |

### Harbor

**Harbor** ialah registry kontena sumber terbuka. Ciri yang kita guna:

- **Imbasan automatik** (Trivy terbina dalam) pada setiap push.
- **Polisi pencegahan**: sekat `pull` imej yang mempunyai kerentanan pada atau melebihi ambang yang ditetapkan.
- **Allowlist CVE**: kecualikan CVE tertentu dengan tarikh luput.
- **Robot account**: kelayakan khusus untuk CI, dengan kebenaran terhad pada satu projek.
- **Kuota** dan kawalan akses mengikut projek.

<div data-fig="aliran-harbor"></div>

> **Perhatian penting.** Docker versi baharu menambah *attestation* (provenance dan SBOM) pada imej yang dibina, lalu imej ditolak sebagai **OCI index** dengan beberapa rujukan. Dalam ujian di server lab ini, polisi pencegahan Harbor **tidak berkuat kuasa** bagi imej index tersebut: `docker pull` berjaya walaupun ambang ditetapkan serendah Low, manakala imej yang sama dibina dengan `--provenance=false --sbom=false` ditolak dengan HTTP 412. Sebab itu semua arahan binaan dalam bengkel ini menggunakan bendera tersebut. Pengajarannya lebih luas: **sahkan bahawa kawalan anda benar-benar menyekat**, jangan hanya percaya ia dihidupkan.

### Trivy di laptop dan Trivy di Harbor

Anda akan menggunakan Trivy di dua tempat. Enjinnya sama, tetapi peranannya berbeza:

| | Trivy di laptop (`alat.sh`) | Trivy di Harbor |
|---|---|---|
| **Cara dijalankan** | Anda taip `trivy ...` (kontena Docker, v0.76.2 dikunci) | Scanner terbina dalam Harbor; berjalan sendiri selepas `docker push` |
| **Apa yang boleh diimbas** | Banyak sasaran: `fs` (kod dan dependency), `config` (Dockerfile, K8s, Terraform), `image` dan secret | Hanya **imej** yang sudah ada dalam Harbor, untuk kerentanan pakej (OS dan bahasa) |
| **Pilihan** | Bebas: `--severity`, `--exit-code`, `.trivyignore`, format output | Tetapan projek: imbas automatik, dan ambang polisi |
| **Keputusan** | Dipaparkan dalam terminal; anda yang bertindak | Disimpan di Harbor (tab *Vulnerabilities*), dan **dikuatkuasakan** |
| **Kesan** | Tiada, melainkan anda menyemak `exit` | Polisi *Prevent vulnerable images from running* pada ambang **High**: imej yang melebihinya ditolak semasa `pull` dengan HTTP 412 |
| **Pangkalan data kerentanan** | Dimuat turun ke laptop anda apabila dijalankan | Dikemas kini oleh Harbor sendiri di server |

Empat perkara yang perlu diingat:

1. **Skop.** Trivy di Harbor tidak memeriksa kod sumber, manifest K8s atau Terraform. Imbasan `fs` dan `config` hanya boleh dibuat di laptop atau CI.
2. **Pintu yang berbeza.** Dalam pipeline (Modul 6), Trivy imej menggagalkan job pada `CRITICAL` **sebelum** `docker push`. Harbor menyekat pada `High` **selepas** imej sampai. Maka imej `High` boleh masuk ke Harbor, tetapi tiada sesiapa boleh menariknya.
3. **Keputusan boleh berbeza.** Imej yang sama boleh memberi bilangan temuan berlainan di laptop dan di Harbor kerana pangkalan data kerentanan dikemas kini pada masa yang berbeza, dan versi Trivy dalam Harbor tidak semestinya v0.76.2.
4. **Harbor ialah kawalan yang tidak boleh dielak.** Imbasan di laptop boleh dilangkau oleh pembangun, tetapi polisi Harbor menyekat imej berisiko semasa `pull` tanpa mengira bagaimana imej itu sampai ke sana.

Ringkasnya, Trivy di laptop ialah alat untuk **menyiasat** (luas, pantas, fleksibel), dan Trivy di Harbor ialah **pintu terakhir** bagi imej (sempit, automatik, mengikat).

---

## Makmal 4.1: Imbas imej

**Tujuan.** Lihat apa yang ada dalam imej yang anda bina pada Modul 0.

<div class="trk trk-a" markdown="1">

```bash
source alat.sh
trivy image --severity HIGH,CRITICAL aspnet-app:latest
docker images aspnet-app:latest --format "saiz: {{.Size}}"
```

</div>

<div class="trk trk-b" markdown="1">

```bash
source alat.sh
trivy image --severity HIGH,CRITICAL laravel-app:latest
docker images laravel-app:latest --format "saiz: {{.Size}}"
```

</div>

Trivy menggunakan soket Docker (disambungkan oleh `alat.sh`) untuk membaca imej tempatan. Imbasan pertama memuat turun pangkalan data kerentanan.

Soalan:

1. Ada berapa bahagian (Target) dalam laporan? Antaranya yang mana OS dan yang mana pakej app?
2. Berapa saiz imej? Kenapa sebesar itu?

<details>
<summary>Jawapan jangkaan</summary>

<div class="trk trk-a" markdown="1">

Imej `aspnet-app:latest` bersaiz **≈ 1.7 GB** kerana ia berasaskan imej **SDK** (`dotnet/sdk`) yang membawa pengkompil dan alat binaan, dan app tidak memerlukannya semasa berjalan. Laporan menyenaraikan bahagian OS (Ubuntu 24.04) dan beberapa fail `*.deps.json` untuk pakej .NET (kerentanan yang sama dilaporkan berulang kali kerana fail itu wujud di beberapa tempat). Bilangan kerentanan High melebihi 10 kerana pengulangan ini.
</div>

<div class="trk trk-b" markdown="1">

Imej `laravel-app:latest` bersaiz **≈ 1 GB** dan membawa **≈ 1,470 kerentanan** (3 Critical, 97 High, 460 Medium, 898 Low): ia berasaskan `php:8.4-cli` (Debian penuh) dengan `git`, `unzip` dan `composer` ditambah. Hampir semuanya pakej OS yang app tidak guna.
</div>
</details>

---

## Makmal 4.2: Imbas Dockerfile

**Tujuan.** Tiga alat, tiga sudut pandang pada fail yang sama.

<div class="trk trk-a" markdown="1">

```bash
hadolint - < aspnet-app/Dockerfile
trivy config aspnet-app
checkov -d aspnet-app --framework dockerfile --compact --quiet
```

</div>

<div class="trk trk-b" markdown="1">

```bash
hadolint - < laravel-app/Dockerfile
trivy config laravel-app
checkov -d laravel-app --framework dockerfile --compact --quiet
```

</div>

Bandingkan: apa yang ditegur oleh setiap alat? Apa yang **tidak** ditegur oleh hadolint tetapi ditegur oleh dua yang lain?

<details>
<summary>Jawapan</summary>

| Isu | hadolint | Trivy config | Checkov |
|---|---|---|---|
| Berjalan sebagai root (tiada `USER`) | ✘ | ✔ DS-0002 (High) | ✔ CKV_DOCKER_3 |
| Tiada `HEALTHCHECK` | ✘ | ✔ DS-0026 (Low) | ✔ CKV_DOCKER_2 |
| `apt-get install` tanpa `--no-install-recommends` | ✔ DL3015 | ✔ DS-0029 (High) | ✘ |
| Pakej `apt` tanpa versi | ✔ DL3008 | ✘ | ✘ |
| Lapisan `apt` tidak dibersihkan | ✔ DL3009 | ✘ | ✘ |

Selepas Modul 1 anda sudah membuang `ENV` yang mengandungi secret, jadi `DS-0031` (Critical) dan `DL3064` yang muncul dalam repo asal tidak lagi kelihatan. hadolint tidak menegur ketiadaan `USER` atau `HEALTHCHECK` sama sekali; itu kebaikan menggunakan lebih daripada satu alat.
</details>

---

## Makmal 4.3: Binaan yang lebih selamat

**Tujuan.** Menggantikan Dockerfile dengan versi yang lebih selamat dan mengukur perbezaan.

Simpan Dockerfile baharu dari bahagian **Fail modul** dan gantikan yang lama:

<div class="trk trk-a" markdown="1">

```bash
cp Dockerfile.aspnet-selamat aspnet-app/Dockerfile
git diff --stat
```

Baca Dockerfile baharu. Perhatikan dua peringkat (`build` dan runtime), `USER app`, `HEALTHCHECK`, dan `apt-get upgrade` sebelum memasang `ping` dan `curl`.

</div>

<div class="trk trk-b" markdown="1">

```bash
cp Dockerfile.laravel-selamat laravel-app/Dockerfile
git diff --stat
```

Baca Dockerfile baharu. Perhatikan dua peringkat, imej asas **Alpine**, `composer install --no-dev`, `USER aplikasi`, `HEALTHCHECK`, dan `APP_DEBUG=false`. Kunci aplikasi (`APP_KEY`) **tidak lagi dibakar** dalam imej: ia dihantar semasa jalan atau dijana sementara.

</div>

Imbas Dockerfile semula, bina imej, dan banding:

<div class="trk trk-a" markdown="1">

```bash
hadolint - < aspnet-app/Dockerfile
trivy config aspnet-app
checkov -d aspnet-app --framework dockerfile --compact --quiet

docker buildx build --provenance=false --sbom=false --load -t aspnet-app:selamat aspnet-app
trivy image --severity HIGH,CRITICAL aspnet-app:selamat
docker images aspnet-app --format "{{.Tag}}: {{.Size}}"
```

Jalankan dan uji (app berjalan sebagai pengguna `app`, bukan root):

```bash
docker rm -f kedai 2>/dev/null
docker run -d --name kedai -p 8080:8080 -e Jwt__Secret="$(openssl rand -hex 16)" aspnet-app:selamat
sleep 6
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/
curl -s "http://localhost:8080/ping?host=127.0.0.1" | grep -oE "bytes from"
docker exec kedai id -un
docker inspect -f '{{.State.Health.Status}}' kedai
docker rm -f kedai
```

</div>

<div class="trk trk-b" markdown="1">

```bash
hadolint - < laravel-app/Dockerfile
trivy config laravel-app
checkov -d laravel-app --framework dockerfile --compact --quiet

docker buildx build --provenance=false --sbom=false --load -t laravel-app:selamat laravel-app
trivy image --severity HIGH,CRITICAL laravel-app:selamat
docker images laravel-app --format "{{.Tag}}: {{.Size}}"
```

Jalankan dan uji (app berjalan sebagai pengguna `aplikasi`, bukan root):

```bash
docker rm -f kedai 2>/dev/null
docker run -d --name kedai -p 8081:8080 laravel-app:selamat
sleep 10
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8081/
curl -s "http://localhost:8081/search?q=laptop" | grep -oE "Laptop[^<]*"
docker exec kedai id -un
docker rm -f kedai
```

</div>

<details>
<summary>Jawapan jangkaan</summary>

<div class="trk trk-a" markdown="1">

- Saiz imej turun daripada ≈ **1.7 GB** kepada ≈ **0.4 GB**.
- `trivy config` dan Checkov tidak melaporkan kegagalan lagi; hadolint hanya memberi `DL3008` (versi pakej `apt` tidak dikunci, amaran yang diterima).
- `trivy image` (selepas Modul 3): tiada kerentanan OS High, dan **satu** High pada pakej app (`SQLitePCLRaw.lib.e_sqlite3`, CVE-2025-6965, tiada versi dibaiki). Pada imej lama ia melaporkan juga OS High dan pengulangan.
- App berjalan sebagai `app`, `ping` masih berfungsi, kesihatan `healthy`. **Kod app masih rentan** (SQL injection di `/login` dan lain-lain, melainkan anda sudah menerapkan tampalan Modul 2): imej yang lebih selamat tidak membaiki kelemahan dalam kod.
</div>

<div class="trk trk-b" markdown="1">

- Saiz imej turun daripada ≈ **1 GB** kepada ≈ **0.2 GB**.
- `trivy config` dan Checkov tidak melaporkan kegagalan lagi; hadolint hanya memberi `DL3018` (versi pakej `apk` tidak dikunci).
- `trivy image`: kerentanan jatuh daripada ≈ **1,470** kepada **≈ 5** (selepas Modul 3: 1 Medium sahaja). Imej Alpine dengan hanya pakej yang diperlukan menghapuskan hampir semua bunyi.
- App berjalan sebagai `aplikasi`, `ping` dan carian berfungsi. **Kod app masih rentan** melainkan anda sudah menerapkan tampalan Modul 2.
</div>

Pengajaran: pengerasan imej dan pembaikan kod ialah dua kerja berbeza. Kedua-duanya perlu.
</details>

---

## Makmal 4.4: Harbor

**Tujuan.** Menolak imej ke registry, melihat imbasan automatik, dan menguji polisi.

Tetapkan nombor peserta anda (contoh `peserta03`):

```bash
P=peserta03
docker login harbor.lab.test -u $P
```

<div class="trk trk-a" markdown="1">

```bash
docker tag aspnet-app:selamat harbor.lab.test/$P/aspnet-app:selamat
docker push harbor.lab.test/$P/aspnet-app:selamat
```

</div>

<div class="trk trk-b" markdown="1">

```bash
docker tag laravel-app:selamat harbor.lab.test/$P/laravel-app:selamat
docker push harbor.lab.test/$P/laravel-app:selamat
```

</div>

Buka <https://harbor.lab.test>, log masuk, pilih projek anda, klik repositori dan artifak. Tunggu beberapa saat hingga status imbasan selesai. Lihat tab **Vulnerabilities**.

Kini uji polisi. Projek anda dikonfigurasi dengan **Prevent vulnerable images from running** pada ambang **High**. Padam imej tempatan dan cuba tarik semula:

<div class="trk trk-a" markdown="1">

```bash
docker rmi harbor.lab.test/$P/aspnet-app:selamat
docker pull harbor.lab.test/$P/aspnet-app:selamat
```

</div>

<div class="trk trk-b" markdown="1">

```bash
docker rmi harbor.lab.test/$P/laravel-app:selamat
docker pull harbor.lab.test/$P/laravel-app:selamat
```

</div>

<details>
<summary>Jawapan: apa yang berlaku?</summary>

<div class="trk trk-a" markdown="1">

`docker pull` **gagal** dengan `412 Precondition Failed`. Imej anda ada satu kerentanan **High**: `CVE-2025-6965` pada `SQLitePCLRaw.lib.e_sqlite3`, yang tidak ada versi dibaiki. Polisi bekerja seperti direka.
</div>

<div class="trk trk-b" markdown="1">

`docker pull` **berjaya**. Imej Alpine anda hanya mempunyai satu kerentanan Medium, di bawah ambang High, jadi polisi membenarkannya. Untuk melihat polisi menyekat, tolak imej lama anda sebagai tag lain: `docker tag laravel-app:latest harbor.lab.test/$P/laravel-app:lama`, push, tunggu imbasan, dan cuba tarik: ia gagal dengan 412.
</div>
</details>

<div class="trk trk-a" markdown="1">

### Terima risiko dengan allowlist

`CVE-2025-6965` tiada versi dibaiki dan anda sudah memutuskan untuk menerimanya buat sementara (Modul 3). Daftarkan dalam Harbor **dengan tarikh luput**. Dalam UI: **Projects → anda → Configuration → CVE allowlist**, pilih **Project allowlist**, tambah `CVE-2025-6965` dan tarikh luput. Atau melalui API (ganti kata laluan Harbor anda dalam `read`):

```bash
read -rs -p "Kata laluan Harbor: " PW; echo
EXP=$(date -d "+30 days" +%s)
curl -s -u $P:$PW -X PUT https://harbor.lab.test/api/v2.0/projects/$P \
  -H "Content-Type: application/json" \
  -d "{\"metadata\":{\"reuse_sys_cve_allowlist\":\"false\"},\"cve_allowlist\":{\"items\":[{\"cve_id\":\"CVE-2025-6965\"}],\"expires_at\":$EXP}}" \
  -o /dev/null -w "%{http_code}\n"
docker pull harbor.lab.test/$P/aspnet-app:selamat
```

Jawapan `200`, dan `docker pull` kini **berjaya**: polisi memberi pengecualian bagi CVE itu sahaja. Perhatikan bahawa pengecualian mempunyai **tarikh luput**, sama seperti `.trivyignore` dalam Modul 3. Ini keputusan yang dicatat, bukan lubang yang dibiarkan.

</div>

> Dalam projek sebenar, siapa yang boleh menukar polisi dan allowlist ialah soal tadbir urus. Dalam makmal ini anda ialah **Project Admin** untuk projek sendiri sahaja; anda tidak boleh melihat atau menolak ke projek orang lain (cuba: `curl -s -o /dev/null -w "%{http_code}\n" -u $P:$PW https://harbor.lab.test/api/v2.0/projects/peserta01/repositories` memberi `403` jika itu bukan projek anda).

---

## Makmal 4.5: IaC: Kubernetes dan Terraform

**Tujuan.** Mengimbas fail konfigurasi infrastruktur dan membaiki Terraform.

Imbas manifest K8s dengan tiga alat:

```bash
trivy config k8s
checkov -d k8s --framework kubernetes --compact --quiet
kube-linter lint k8s
```

Imbas Terraform:

```bash
trivy config terraform
checkov -d terraform --framework terraform --compact --quiet
```

Soalan:

1. Berapa temuan setiap alat untuk `k8s/aspnet.yaml`?
2. Apa temuan Terraform yang paling serius? Tulis ancamannya dengan bahasa STRIDE.
3. Manifest K8s ada secret dalam `env`. Alat mana menangkapnya?

<details>
<summary>Jawapan jangkaan</summary>

| Alat | `k8s/aspnet.yaml` | `terraform/main.tf` |
|---|---|---|
| Trivy config | 21 | 18 (1 Critical, 9 High) |
| Checkov | 21 | 21 (+ 1 temuan secret) |
| kube-linter | 10 (laravel: 9) | tidak berkaitan |

Terraform paling serius: **kumpulan keselamatan membenarkan SSH daripada `0.0.0.0/0`** dan **pangkalan data awam tanpa penyulitan dengan kata laluan dalam kod**. Dalam STRIDE: Information disclosure (data DB boleh dibaca) dan Elevation of privilege (SSH dibuka kepada dunia).

Secret dalam `env` manifest K8s: hanya **kube-linter** (`env-var-secret`) yang menegurnya, dan hanya bagi pemboleh ubah yang namanya mengandungi `secret`/`password` (ia menangkap `Jwt__Secret` tetapi bukan `PAYMENT_API_KEY`). Gitleaks lalai dan Trivy tidak menangkapnya; peraturan custom Modul 1 menangkap kedua-duanya.
</details>

Kini baiki Terraform. Simpan `main-selamat.tf` (bahagian **Fail modul**), gantikan fail asal, dan imbas semula:

```bash
cp main-selamat.tf terraform/main.tf
trivy config terraform
checkov -d terraform --framework terraform --compact --quiet
```

Baca perubahan: akses awam disekat pada bucket S3, SSH dihadkan kepada rangkaian admin, pangkalan data tidak lagi awam dan disulitkan, dan kata laluan datang daripada pemboleh ubah `sensitive` bukan kod. Perhatikan juga komen `#trivy:ignore:AWS-0107`: HTTPS awam sengaja dibuka kepada internet, dan pengecualian itu dicatat **dengan alasan** di sebelah kod.

<details>
<summary>Jawapan jangkaan</summary>

Trivy turun daripada **18** kepada **2** temuan (kedua-duanya Low), dan Checkov daripada **21** kepada **9**. Baki Checkov termasuk amalan lanjutan seperti pencatatan akses S3 dan replikasi silang kawasan, yang mungkin atau mungkin tidak relevan untuk app anda: putuskan, jangan ikut membuta tuli.
</details>

Pembaikan manifest K8s dibuat dalam [Modul 7](../modul-7-hardening/README.md), apabila anda belajar `securityContext`, Pod Security Standards dan NetworkPolicy.

---

## Makmal 4.6: Robot account untuk CI

**Tujuan.** Menyediakan kelayakan yang akan digunakan CI pada Hari 4, tanpa menggunakan kata laluan peribadi anda.

Dalam UI Harbor: **Projects → anda → Robot Accounts → New Robot Account**. Beri nama `ci`, tempoh luput 30 hari, dan benarkan **Push** dan **Pull** artifak serta **Create** imbasan. Salin **rahsia** yang dipaparkan: ia hanya dipaparkan sekali.

Sahkan:

```bash
echo 'RAHSIA_ROBOT' | docker login harbor.lab.test -u 'robot$'$P'+ci' --password-stdin
```

Robot hanya boleh bertindak dalam projek anda; percubaan menolak ke projek lain memberi ralat.

> Simpan rahsia robot di tempat selamat (pengurus kata laluan) untuk Modul 6. Ia ialah secret sebenar walaupun dalam makmal, dan ia tidak boleh masuk ke git.

## Senarai semak Modul 4

- [ ] Saya mengimbas imej dan tahu dari mana kerentanan datang
- [ ] Saya membandingkan hadolint, Trivy config dan Checkov pada Dockerfile
- [ ] Saya menggantikan Dockerfile, membina imej yang lebih kecil dan app masih berfungsi sebagai bukan root
- [ ] Saya menolak imej ke Harbor, melihat imbasan, dan menguji polisi (pull ditolak atau dibenarkan)
- [ ] Saya faham kenapa binaan menggunakan `--provenance=false --sbom=false`
- [ ] Saya mengimbas K8s dan Terraform, dan membaiki Terraform
- [ ] Saya mencipta robot account `ci` dan menyimpan rahsianya dengan selamat

## Rujukan

- Harbor: <https://goharbor.io/docs/>
- Trivy untuk imej dan konfigurasi: <https://trivy.dev>
- Panduan Dockerfile: <https://docs.docker.com/build/building/best-practices/>
- OWASP Docker Security Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html>
