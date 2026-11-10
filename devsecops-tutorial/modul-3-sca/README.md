# Modul 3: SCA, SBOM dan pakej yang direka AI

**Hari 2, 2:00 hingga 5:00 petang**

Dalam modul ini anda akan:

1. Faham SCA (Software Composition Analysis): pakej langsung dan **transitif**, fail kunci (lock file), dan pangkalan data vulnerability.
2. Menjalankan alat asal ekosistem (`dotnet list package`, `composer audit`) dan **Trivy**, dan membandingkan hasilnya.
3. Membaiki vulnerability dengan menaikkan versi, dan memutuskan apa yang dilakukan bila **tiada versi yang dibaiki**.
4. Menjana **SBOM** (CycloneDX) dengan Trivy dan Syft, dan mengimbas SBOM itu.
5. Menyemak pakej yang **dicadangkan AI** sebelum menambahnya, kerana pakej itu mungkin tidak wujud.

> Prasyarat: [Modul 2](../modul-2-sast/README.md) siap. Fungsi `dotnet`, `composer`, `trivy` dan `syft` dalam `alat.sh` berfungsi (muat semula `alat.sh` yang terkini, ia ditambah fungsi baharu). App anda sudah dibina sebagai imej `aspnet-app:latest` atau `laravel-app:latest`.

## Jadual

| Masa | Aktiviti |
|---|---|
| 2:00 – 2:30 | Teori: SCA, transitif, lock file, SBOM, pakej direka AI |
| 2:30 – 3:15 | Makmal 3.1 dan 3.2: audit asal dan Trivy |
| 3:15 – 3:30 | Rehat |
| 3:30 – 4:05 | Makmal 3.3 dan 3.4: baiki, terima risiko |
| 4:05 – 4:40 | Makmal 3.5: SBOM |
| 4:40 – 5:00 | Makmal 3.6: pakej direka AI dan semakan |

---

## Teori ringkas

### Apa itu SCA

Kebanyakan kod dalam app anda bukan anda yang tulis. **SCA** membaca senarai pakej yang anda guna dan memadankannya dengan pangkalan data vulnerability yang diketahui (CVE, GitHub Advisory dan lain-lain). Ia menjawab: *"pakej versi ini ada masalah yang diketahui?"*

- **Langsung (direct)**: pakej yang anda tambah sendiri dalam `.csproj` atau `composer.json`.
- **Transitif**: pakej yang dibawa oleh pakej lain. Anda tidak memilihnya tetapi anda tetap menjalankannya.
- **Fail kunci (lock file)** merekod versi **tepat** yang digunakan: `packages.lock.json` (.NET), `composer.lock` (PHP). Alat SCA membaca fail ini kerana ia menyatakan apa yang sebenarnya dipasang, bukan julat yang dibenarkan.

### Apa SCA tidak boleh lakukan

- Ia memberitahu pakej **ada** vulnerability, bukan sama ada kod anda **menggunakan** bahagian yang vulnerable.
- Vulnerability yang baru ditemui tidak akan ada hingga pangkalan data dikemas kini. Imbas **berkala**, bukan sekali.
- Keterukan (High) ialah skor umum, bukan kesan sebenar pada app anda. Konteks anda menentukan keutamaan.

### SBOM

**SBOM** (Software Bill of Materials) ialah senarai komponen dalam perisian anda, seperti senarai bahan pada bungkusan. Dua format piawai: **CycloneDX** dan **SPDX**. Gunanya: apabila vulnerability baharu diumumkan (seperti Log4Shell), anda boleh menyoal SBOM yang disimpan untuk tahu **serta-merta** app mana terjejas, tanpa mengimbas semula semua.

**VEX** ialah pasangan SBOM: dokumen yang menyatakan sama ada sesuatu vulnerability benar-benar boleh dieksploit dalam produk anda (`not_affected`, `affected`, `fixed`). Ia mengurangkan bunyi.

### Pakej yang direka oleh AI

Model bahasa kadang-kadang mencadangkan nama pakej yang **tidak wujud**. Penyerang boleh mendaftarkan nama itu di registry awam dengan kod berniat jahat, dan sesiapa yang menyalin cadangan AI akan memasangnya. Ini dipanggil **slopsquatting**. Ia berkait dengan **typosquatting** (nama hampir sama dengan pakej popular) dan **dependency confusion** (nama pakej dalaman didaftarkan di registry awam).

Kawalan asas: **semak pakej wujud**, semak **umur, jumlah unduh dan pemilik**, guna fail kunci, dan gunakan suapan peribadi untuk pakej dalaman.

---

## Makmal 3.1: Audit asal ekosistem

**Tujuan.** Menggunakan alat yang sudah ada dalam ekosistem anda.

<div class="trk trk-a" markdown="1">

```bash
source alat.sh
cd aspnet-app
dotnet list package --vulnerable --include-transitive
cd ..
```

NuGet juga memberi amaran `NU1902`/`NU1903` semasa `dotnet restore` dan binaan.

</div>

<div class="trk trk-b" markdown="1">

```bash
source alat.sh
cd laravel-app
composer audit --locked
cd ..
```

`--locked` membaca `composer.lock` kerana folder `vendor/` tidak wujud pada klon baharu.

</div>

Soalan:

1. Berapa pakej terjejas? Mana yang langsung dan mana yang transitif?
2. Berapa tahap keterukan?

<details>
<summary>Jawapan</summary>

<div class="trk trk-a" markdown="1">

**4 pakej**: dua langsung (`Newtonsoft.Json 12.0.3` High; `SharpZipLib 1.3.2` High dan dua Moderate), dan dua **transitif yang tidak kita rancang**: `Microsoft.OpenApi 2.0.0` (dibawa oleh `Microsoft.AspNetCore.OpenApi`) dan `SQLitePCLRaw.lib.e_sqlite3 2.1.11` (dibawa oleh `Microsoft.Data.Sqlite`). Vulnerability transitif tidak kelihatan dalam `.csproj`; hanya alat yang membaca graf penuh menunjukkannya.
</div>

<div class="trk trk-b" markdown="1">

**4 advisori pada 2 pakej**: `firebase/php-jwt 5.0.0` (CVE-2021-46743 **critical**, CVE-2025-45769 low) dan `phpmailer/phpmailer 6.4.1` (CVE-2021-34551 dan CVE-2021-3603, kedua-duanya high).
</div>
</details>

---

## Makmal 3.2: Imbas dengan Trivy

**Tujuan.** Menggunakan satu alat yang sama untuk semua ekosistem, dan memahami syaratnya.

<div class="trk trk-a" markdown="1">

```bash
trivy fs --scanners vuln aspnet-app
```

Kemudian lihat apa yang berlaku **tanpa fail kunci**:

```bash
mv aspnet-app/packages.lock.json /tmp/
trivy fs --scanners vuln aspnet-app
mv /tmp/packages.lock.json aspnet-app/
```

</div>

<div class="trk trk-b" markdown="1">

```bash
trivy fs --scanners vuln laravel-app
```

Trivy membaca `composer.lock` terus.

</div>

<details>
<summary>Jawapan</summary>

<div class="trk trk-a" markdown="1">

Dengan `packages.lock.json`, Trivy melaporkan **6 CVE** pada 4 pakej (empat High, dua Medium; `SharpZipLib` ada tiga CVE). **Tanpa fail kunci, Trivy melaporkan 0**: ia tidak membaca `.csproj`, jadi ia tidak tahu versi yang dipasang. Repo ini menyertakan fail itu dan `<RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>` dalam `.csproj`. Dalam projek anda sendiri, **tambah ini** jika mahu SCA yang boleh dipercayai, dan commit fail kunci itu.
</div>

<div class="trk trk-b" markdown="1">

Trivy melaporkan **4 CVE** (1 Critical, 2 High, 1 Low), sepadan dengan `composer audit`. Pada PHP fail kunci sudah menjadi amalan standard, jadi ia berfungsi tanpa langkah tambahan.
</div>

Pengajaran: **dua alat boleh bersetuju**, tetapi satu alat boleh diam kerana prasyaratnya tidak dipenuhi. "Tiada temuan" mesti dibaca bersama "adakah alat itu dapat membaca apa yang perlu dibaca?".
</details>

---

## Makmal 3.3: Baiki dengan menaikkan versi

**Tujuan.** Menaikkan pakej yang ada versi dibaiki, dan sahkan app masih berfungsi.

<div class="trk trk-a" markdown="1">

```bash
cd aspnet-app
dotnet add package Newtonsoft.Json --version 13.0.3
dotnet add package SharpZipLib --version 1.4.2
dotnet add package Microsoft.OpenApi --version 2.7.5
dotnet list package --vulnerable --include-transitive
cd ..
```

Perhatikan trik pada baris ketiga: `Microsoft.OpenApi` ialah pakej **transitif**. Dengan menambahnya sebagai pakej langsung pada versi yang lebih baharu, anda **menimpa** versi yang dibawa secara transitif. Ini cara biasa membaiki vulnerability transitif apabila pakej induk belum dikemas kini.

</div>

<div class="trk trk-b" markdown="1">

```bash
cd laravel-app
composer require "phpmailer/phpmailer:^6.10" "firebase/php-jwt:^7.0" --no-interaction --no-audit
composer audit --locked
cd ..
```

`--no-audit` menahan audit semasa `require` supaya anda melihat hasil audit secara berasingan selepas itu. `^6.10` bermaksud versi 6.10 atau lebih baharu dalam siri 6.

</div>

Sahkan hasilnya dan pastikan app masih berfungsi. Bina semula, jalankan dan cuba satu titik akhir:

<div class="trk trk-a" markdown="1">

```bash
trivy fs --scanners vuln aspnet-app
docker rm -f kedai 2>/dev/null
docker buildx build --provenance=false --sbom=false --load -t aspnet-app:sca aspnet-app
docker run -d --name kedai -p 8080:8080 aspnet-app:sca && sleep 5
curl -s -X POST http://localhost:8080/api/import -d '{"a":1}' -H "Content-Type: application/json"; echo
docker rm -f kedai
```

</div>

<div class="trk trk-b" markdown="1">

```bash
trivy fs --scanners vuln laravel-app
docker rm -f kedai 2>/dev/null
docker buildx build --provenance=false --sbom=false --load -t laravel-app:sca laravel-app
docker run -d --name kedai -p 8081:8080 laravel-app:sca && sleep 8
curl -s -X POST http://localhost:8081/api/import -d 'data=i:1;'; echo
docker rm -f kedai
```

</div>

<details>
<summary>Jawapan</summary>

<div class="trk trk-a" markdown="1">

Vulnerability turun daripada **6 CVE** kepada **1**: `SQLitePCLRaw.lib.e_sqlite3` (CVE-2025-6965, High) kekal **tanpa versi dibaiki**. App masih berjalan dan `/api/import` memulangkan `JObject`. Semak `git diff` untuk `AspNetLab.csproj` dan `packages.lock.json`.
</div>

<div class="trk trk-b" markdown="1">

`composer audit --locked` memberi `No security vulnerability advisories found` dan Trivy memberi `Clean`. Composer menaikkan `firebase/php-jwt` kepada 7.x dan `phpmailer/phpmailer` kepada 6.12. App masih berjalan dan `/api/import` memulangkan `integer`. Perhatikan: lompatan versi utama (`5` ke `7`) boleh memecahkan API; dalam app sebenar anda perlu menjalankan ujian dan membaca nota pelepasan. App lab tidak memanggil `php-jwt`, jadi tiada kesan.
</div>
</details>

---

## Makmal 3.4: Bila tiada versi yang dibaiki

**Tujuan.** Membuat keputusan dengan sedar bila anda tidak boleh membaiki, dan menjadikan imbasan sebagai pintu.

<div class="trk trk-a" markdown="1">

Baki CVE-2025-6965 (`SQLitePCLRaw.lib.e_sqlite3`) tiada versi dibaiki. Pilihan anda: tunggu pembaikan, ganti pakej, atau **terima risiko** dengan alasan. Rekod penerimaan dalam fail `.trivyignore` **dengan tarikh luput**:

```bash
echo "CVE-2025-6965 exp:2027-01-31" > .trivyignore
trivy fs --scanners vuln aspnet-app
```

Anda akan melihat `Clean`. Tarikh luput memaksa semakan semula: selepas itu temuan muncul semula.

</div>

<div class="trk trk-b" markdown="1">

Semua vulnerability sudah dibaiki. Untuk melihat cara terima risiko, andaikan anda mahu mengabaikan CVE-2021-34551 buat sementara (anda tidak perlu benar-benar melakukannya):

```bash
git stash          # simpan pembaikan anda
trivy fs --scanners vuln laravel-app | grep -c CVE
echo "CVE-2021-34551 exp:2027-01-31" > .trivyignore
trivy fs --scanners vuln laravel-app | grep -c CVE
rm .trivyignore
git stash pop
```

Bilangan CVE turun satu apabila dimasukkan dalam `.trivyignore`.

</div>

**Pintu CI.** Untuk menggagalkan pipeline bila ada vulnerability serius:

<div class="trk trk-a" markdown="1">

```bash
trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 aspnet-app; echo "exit=$?"
rm -f .trivyignore
trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 aspnet-app >/dev/null; echo "tanpa pengecualian exit=$?"
```

</div>

<div class="trk trk-b" markdown="1">

```bash
trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 laravel-app; echo "exit=$?"
```

</div>

`--exit-code 1` menjadikan Trivy memulangkan `1` bila ada temuan, yang menggagalkan job CI. Tanpa pengecualian `.trivyignore`, **Trek A** memberi `exit=1` kerana `e_sqlite3` kekal.

> Pilihan `--ignore-unfixed` menyembunyikan vulnerability tanpa versi dibaiki. Ia mengurangkan bunyi tetapi juga menyembunyikan risiko sebenar. Guna dengan sedar, dan rekodkan keputusan, bukan sekadar menghidupkan bendera.

---

## Makmal 3.5: SBOM

**Tujuan.** Menjana SBOM, melihat perbezaan alat, dan mengimbasnya.

<div class="trk trk-a" markdown="1">

```bash
trivy fs --quiet --format cyclonedx --output sbom-fs.cdx.json aspnet-app
trivy image --quiet --format cyclonedx --output sbom-imej.cdx.json aspnet-app:latest
syft dir:aspnet-app -q -o cyclonedx-json=sbom-syft.cdx.json
syft docker:aspnet-app:latest -q -o cyclonedx-json=sbom-syft-imej.cdx.json
```

</div>

<div class="trk trk-b" markdown="1">

```bash
trivy fs --quiet --format cyclonedx --output sbom-fs.cdx.json laravel-app
trivy image --quiet --format cyclonedx --output sbom-imej.cdx.json laravel-app:latest
syft dir:laravel-app -q -o cyclonedx-json=sbom-syft.cdx.json
syft docker:laravel-app:latest -q -o cyclonedx-json=sbom-syft-imej.cdx.json
```

</div>

Kira komponen dalam setiap SBOM:

```bash
for f in sbom-*.json; do
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(sys.argv[1], len(d['components']), 'komponen')" "$f"
done
```

Imbas SBOM itu (tanpa kod sumber atau imej):

```bash
trivy sbom --quiet --severity HIGH,CRITICAL sbom-fs.cdx.json
```

Format SPDX tersedia dengan `--format spdx-json`.

<details>
<summary>Jawapan jangkaan</summary>

<div class="trk trk-a" markdown="1">

| SBOM | Komponen |
|---|---|
| Trivy fs (kod sumber) | 11 |
| Syft dir | 11 |
| Trivy image | ≈ 814 |
| Syft image | ≈ 10,900 |

</div>

<div class="trk trk-b" markdown="1">

| SBOM | Komponen |
|---|---|
| Trivy fs (kod sumber) | 80 |
| Syft dir | 80 |
| Trivy image | ≈ 309 |
| Syft image | ≈ 8,800 |

</div>

Untuk SBOM **kod sumber**, kedua-dua alat sepakat. Untuk SBOM **imej**, bilangan sangat berbeza: Syft juga menyenaraikan beribu-ribu **fail** (jenis `file`) selain pakej, manakala Trivy hanya menyenaraikan pakej dan aplikasi. Bilangan komponen bukan ukuran "lebih baik"; pilih mengikut apa yang pengguna SBOM perlukan.

`trivy sbom` mengimbas SBOM **tanpa** akses ke kod atau imej asal. Inilah kegunaan sebenar SBOM: simpan satu pada setiap pelepasan, dan bila CVE baharu diumumkan, imbas SBOM yang disimpan itu.
</details>

Bersihkan: `rm -f sbom-*.json`.

---

## Makmal 3.6: Pakej yang direka AI

**Tujuan.** Membiasakan diri menyemak pakej sebelum memasangnya.

Simpan `semak-pakej.sh` (bahagian **Fail modul**) dalam folder repo dan beri kebenaran jalan: `chmod +x semak-pakej.sh`. Skrip ini menyemak sama ada pakej wujud, dan menunjukkan umur, jumlah unduh dan pemilik.

Bayangkan anda bertanya asisten AI "pakej apa untuk membersihkan input HTML?" dan ia mencadangkan dua nama. Semak kedua-duanya:

<div class="trk trk-a" markdown="1">

```bash
./semak-pakej.sh nuget HtmlSanitizer
./semak-pakej.sh nuget Kedai.Security.InputSanitizer.Pro
```

</div>

<div class="trk trk-b" markdown="1">

```bash
./semak-pakej.sh packagist ezyang/htmlpurifier
./semak-pakej.sh packagist laravel/secure-sanitizer-pro
```

</div>

Soalan:

1. Pakej mana yang wujud? Apa yang memberi keyakinan bahawa ia boleh dipercayai?
2. Apa yang akan berlaku jika penyerang mendaftarkan nama yang tidak wujud itu esok?
3. Tulis senarai semak tiga langkah anda sendiri sebelum menambah pakej baharu.

<details>
<summary>Jawapan</summary>

<div class="trk trk-a" markdown="1">

`HtmlSanitizer` wujud dengan beratus juta unduhan dan 147 versi: ciri pakej yang matang. `Kedai.Security.InputSanitizer.Pro` memberi `TIDAK WUJUD` (HTTP 404): ia direka.

</div>

<div class="trk trk-b" markdown="1">

`ezyang/htmlpurifier` wujud sejak 2012 dengan jutaan unduhan. `laravel/secure-sanitizer-pro` memberi `TIDAK WUJUD` (HTTP 404): ia direka. Perhatikan awalan `laravel/` yang menyerupai organisasi rasmi tetapi tidak ada; ini yang menjadikan nama direka kelihatan meyakinkan.

</div>

Jika penyerang mendaftarkan nama itu esok, pakej itu **wujud** dan lulus semakan "wujud". Itulah kenapa semakan wujud sahaja **tidak cukup**: umur yang sangat baharu, jumlah unduh hampir sifar, dan pemilik yang tidak dikenali ialah isyarat bahaya. Senarai semak contoh: (1) wujud dan bukan baharu; (2) unduhan dan pemilik munasabah; (3) repositori sumber dan penyelenggara boleh disahkan, dan pakej disambungkan melalui fail kunci supaya versi tidak bertukar senyap-senyap.
</details>

## Senarai semak Modul 3

- [ ] Saya menjalankan audit asal ekosistem dan Trivy, dan faham bezanya
- [ ] Saya tahu kenapa Trivy tidak melihat pakej .NET tanpa `packages.lock.json` (Trek A) atau kenapa `composer audit` memerlukan `--locked` (Trek B)
- [ ] Saya menaikkan versi pakej, mengesahkan app masih berfungsi, dan melihat vulnerability turun
- [ ] Saya tahu cara terima risiko dengan `.trivyignore` yang ada tarikh luput, dan cara menjadikan Trivy pintu dengan `--exit-code 1`
- [ ] Saya menjana SBOM kod sumber dan imej, dan mengimbas SBOM dengan `trivy sbom`
- [ ] Saya menyemak pakej yang dicadangkan AI sebelum menambahnya

## Rujukan

- Trivy: <https://trivy.dev>
- CycloneDX: <https://cyclonedx.org> · SPDX: <https://spdx.dev>
- OpenVEX: <https://github.com/openvex/spec>
- NuGet audit: <https://learn.microsoft.com/nuget/concepts/auditing-packages>
- Composer audit: <https://getcomposer.org/doc/03-cli.md#audit>
