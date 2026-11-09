# Modul 1: Secret Detection dan secrets management

**Hari 1, 2:00 hingga 5:00 petang**

Dalam modul ini anda akan:

1. Faham kenapa secret yang pernah di-commit kekal dalam sejarah git walaupun fail sudah dipadam.
2. Menjalankan **Gitleaks** pada working tree dan pada sejarah git, dan membaca hasilnya.
3. Menulis **peraturan tersuai** untuk menangkap secret yang peraturan lalai terlepas.
4. Membandingkan dengan pengimbas secret **Trivy** dan memahami titik buta setiap alat.
5. Memasang **pre-commit hook** yang menghalang secret daripada di-commit.
6. Mengeluarkan secret daripada kod, menggunakan **baseline** untuk temuan lama, dan mengikut urutan tindak balas apabila secret bocor.

> Prasyarat: [Persediaan](../00-persediaan/README.md) siap dan `source alat.sh` berfungsi.

Semua arahan dalam modul ini (dan modul seterusnya) dijalankan dari **akar repo lab**. Mulakan setiap sesi terminal baharu dengan:

```bash
cd ~/devsecops-lab
source alat.sh
ls
```

`ls` mesti menunjukkan `README.md`, `aspnet-app`, `k8s`, `laravel-app`, `terraform` dan `alat.sh`. Folder `k8s/` (manifest Kubernetes) dan `terraform/` ialah sebahagian daripada repo lab yang anda klon, bukan fail yang anda cipta. Jika `ls` tidak menunjukkannya, anda bukan dalam folder yang betul, atau repo belum diklon (Persediaan 2).

> **Gitleaks tidak dipasang pada laptop anda.** Ia berjalan dalam kontena Docker melalui fungsi `gitleaks` dalam `alat.sh`. Semak dengan `gitleaks version`, yang mesti memberi `v8.30.1`. Jika terminal memberi `gitleaks: command not found`, jalankan `source alat.sh` dahulu. Kontena itu hidup beberapa saat sahaja dan dipadam apabila imbasan tamat, jadi ia tidak akan muncul dalam `docker ps`; itu normal.

## Jadual

| Masa | Aktiviti |
|---|---|
| 2:00 – 2:30 | Teori: jenis secret, cara pengesanan, kenapa sejarah git penting |
| 2:30 – 3:15 | Makmal 1.1 dan 1.2: imbas working tree dan sejarah |
| 3:15 – 3:30 | Rehat |
| 3:30 – 4:00 | Makmal 1.3 dan 1.4: peraturan tersuai, bandingkan Trivy |
| 4:00 – 4:40 | Makmal 1.5 dan 1.6: pre-commit, baiki, baseline |
| 4:40 – 5:00 | Secrets management dan semakan |

---

## Teori ringkas

### Apa yang dikira secret

Kata laluan pangkalan data, kunci API, token akses, kunci peribadi, rentetan sambungan dan `APP_KEY` sesebuah framework. Apabila satu daripadanya sampai ke git, anggap ia **sudah bocor**: sesiapa yang pernah klon repo, fork, atau lihat cache CI mempunyainya.

### Kenapa sejarah git penting

Memadam fail dalam commit baharu **tidak** memadamkan ia daripada sejarah. Perintah `git log -p` atau klon lama masih menunjukkannya. Dalam repo lab, `appsettings.Production.json` (Trek A) dan `.env` (Trek B) pernah di-commit dan kemudian dibuang; anda akan melihat bahawa imbasan folder biasa **tidak nampak** tetapi imbasan sejarah **nampak**.

### Cara alat mengesan

| Teknik | Cara | Kelebihan | Kelemahan |
|---|---|---|---|
| Regex mengikut pembekal | Corak token tertentu (cth awalan kunci pembekal awan) | Tepat, sedikit positif palsu | Hanya format yang dikenali |
| Kata kunci + entropi | Nama pemboleh ubah (`password`, `api_key`) dengan nilai rawak | Menangkap secret generik | Positif palsu dan terlepas |
| Pengesahan aktif | Cuba guna secret pada API pembekal | Mengesahkan secret masih hidup | Perlu rangkaian; sesetengah organisasi tidak membenarkan |

**Gitleaks** menggunakan dua teknik pertama dan pantas. **TruffleHog** menambah pengesahan aktif. Dalam bengkel ini kita guna Gitleaks sebagai alat utama kerana ia ringan dan senang diserap ke dalam pre-commit dan CI.

Secret palsu dalam repo lab sengaja **tidak** menyerupai format token pembekal sebenar, supaya GitHub tidak menyekat push repo lab. Itu bermakna ia ditangkap oleh peraturan generik (`generic-api-key`), bukan peraturan khusus pembekal.

---

## Makmal 1.1: Imbas working tree

**Tujuan.** Cari secret dalam fail semasa.

<div class="trk trk-a" markdown="1">

```bash
source alat.sh
gitleaks dir aspnet-app --no-banner --redact=100 -f csv -r - -l error | cut -d, -f1,2,6
```

</div>

<div class="trk trk-b" markdown="1">

```bash
source alat.sh
gitleaks dir laravel-app --no-banner --redact=100 -f csv -r - -l error | cut -d, -f1,2,6
```

</div>

`--redact=100` menyembunyikan nilai secret dalam output, satu tabiat baik supaya hasil imbasan sendiri tidak membocorkan secret ke log CI.

Soalan:

1. Berapa banyak temuan? Dalam fail mana?
2. Peraturan mana yang menangkapnya?
3. Adakah semua temuan itu secret sebenar?

<details>
<summary>Jawapan</summary>

Setiap trek menemui **4** secret, semuanya dengan peraturan `generic-api-key`.

<div class="trk trk-a" markdown="1">

`aspnet-app/Dockerfile` (ENV `Jwt__Secret`), dan tiga dalam `aspnet-app/appsettings.json` (kata laluan pangkalan data dalam rentetan sambungan, `Jwt:Secret`, `Pembayaran:ApiKey`).

</div>

<div class="trk trk-b" markdown="1">

`laravel-app/Dockerfile` (ENV `PAYMENT_API_KEY`), dan tiga dalam `laravel-app/config/kedai.php` (`payment_api_key`, `mail_password`, `db_admin_password`).

</div>

Semua nilai adalah palsu, tetapi alat tidak tahu itu; anda yang perlu menilai (triage) dalam projek sebenar.
</details>

---

## Makmal 1.2: Imbas sejarah git

**Tujuan.** Cari secret yang sudah dibuang daripada kod tetapi masih dalam sejarah.

```bash
git log --oneline
gitleaks git . --no-banner --no-color --redact=100 -l error -v 2>&1 | grep -E "^(File|Commit):" | paste - - | sed -E 's/Commit: (.{7})[0-9a-f]*/\1/'
```

Baris pertama memaparkan commit. Baris kedua mengimbas **semua** commit dan meringkaskan setiap temuan sebagai fail dan commit.

Soalan:

1. Berapa banyak temuan sejarah berbanding temuan working tree dalam Makmal 1.1 (untuk seluruh repo, lihat `gitleaks dir . --no-banner`)?
2. Fail mana yang hanya muncul dalam sejarah?
3. Jika fail itu sudah tiada, adakah secret di dalamnya selamat?

<details>
<summary>Jawapan</summary>

Seluruh repo memberi **15** temuan sejarah berbanding **9** pada working tree. Enam yang tambahan hanya wujud dalam sejarah:

- `aspnet-app/appsettings.Production.json` (3 temuan): ditambah dalam satu commit dan dibuang dalam commit berikutnya.
- `laravel-app/.env` (3 temuan): fail `.env` yang di-commit secara paksa kemudian dibuang.

Secret itu **tidak selamat**. Sesiapa yang klon repo boleh melihatnya dengan `git show <commit>:laluan/fail`. Satu-satunya tindakan yang menyelesaikan masalah ialah **putar (rotate)** secret itu, iaitu cipta yang baharu dan batalkan yang lama.
</details>

---

## Makmal 1.3: Peraturan tersuai

**Tujuan.** Menangkap secret yang peraturan lalai terlepas.

Folder `k8s/` ialah manifest Kubernetes dalam repo lab (`namespace.yaml`, `aspnet.yaml` dan `laravel.yaml`). Dari akar repo lab, jalankan imbasan padanya. Jika Gitleaks melapor bahawa `k8s` tidak wujud, anda bukan dalam `~/devsecops-lab`:

```bash
gitleaks dir k8s --no-banner -l error; echo "exit=$?"
```

Hasilnya `exit=0`, tiada temuan. Tetapi lihat `k8s/aspnet.yaml`:

```bash
grep -n -B1 -A1 Secret k8s/aspnet.yaml
```

Terdapat `value: "..."` bagi pemboleh ubah `Jwt__Secret`. Peraturan lalai terlepas kerana **nama dan nilai berada pada dua baris berasingan**.

Simpan fail `gitleaks-lab.toml` (bahagian **Fail modul**) dalam folder repo, kemudian:

```bash
gitleaks dir k8s --no-banner -c gitleaks-lab.toml --redact=100 -l error; echo "exit=$?"
```

Kini kedua-dua fail K8s ditangkap oleh peraturan `k8s-env-secret`. Buka `gitleaks-lab.toml` dan baca peraturan itu: `regex` memadankan `name:` yang mengandungi `secret`, `password`, `api_key` atau `token`, melintasi baris baharu, dan menangkap `value:` sebagai kumpulan rahsia.

Soalan: apakah fungsi medan `path` dan `keywords` dalam peraturan? Apakah risikonya jika `regex` terlalu longgar?

<details>
<summary>Jawapan</summary>

`path` mengehadkan peraturan kepada fail `.yaml`/`.yml` sahaja, dan `keywords` ialah penapis pantas: Gitleaks hanya menjalankan regex yang mahal pada fail yang mengandungi perkataan itu. Peraturan yang terlalu longgar menghasilkan banyak positif palsu, dan pasukan akan mula mengabaikan semua temuan. Mulakan sempit, ukur, kemudian longgarkan.
</details>

---

## Makmal 1.4: Bandingkan dengan Trivy

**Tujuan.** Sedar bahawa alat berbeza mempunyai titik buta berbeza.

Trivy juga ada pengimbas secret:

<div class="trk trk-a" markdown="1">

```bash
source alat.sh
trivy fs --scanners secret aspnet-app
```

</div>

<div class="trk trk-b" markdown="1">

```bash
source alat.sh
trivy fs --scanners secret laravel-app
```

</div>

Anda tidak akan melihat temuan. Bandingkan dengan pengimbas **konfigurasi** Trivy, yang membaca Dockerfile:

```bash
trivy config --severity CRITICAL .
```

<details>
<summary>Jawapan</summary>

Pengimbas `secret` Trivy mencari corak token pembekal yang dikenali. Secret palsu kita sengaja tidak mengikut format itu, jadi ia terlepas sepenuhnya. Namun `trivy config` menemui `DS-0031` (CRITICAL) pada Dockerfile: peraturan konfigurasi menegur **ENV yang namanya mengandungi `secret`/`key`**, tanpa melihat nilainya.

Kesimpulan: gunakan lebih daripada satu pendekatan. Gitleaks menangkap nilai, peraturan konfigurasi menangkap nama, dan keduanya melengkapi satu sama lain.
</details>

---

## Makmal 1.5: Pre-commit hook

**Tujuan.** Menghalang secret daripada sampai ke git.

Cipta hook yang mengimbas hanya perubahan yang dipentaskan (staged):

```bash
cat > .git/hooks/pre-commit <<'EOF'
#!/usr/bin/env bash
source "$(git rev-parse --show-toplevel)/alat.sh" >/dev/null
gitleaks git --pre-commit --staged --redact --no-banner
EOF
chmod +x .git/hooks/pre-commit
```

Uji dengan secret palsu:

```bash
echo 'api_key = "Zq8w3kLm2Pv9Xb7Nc4Rt6Yh1"' > rahsia-ujian.txt
git add rahsia-ujian.txt
git commit -m "uji pre-commit"; echo "exit=$?"
```

Commit mesti **gagal** (`exit=1`) dan Gitleaks memaparkan `leaks found: 1`. Bersihkan:

```bash
git rm -q --cached rahsia-ujian.txt
rm rahsia-ujian.txt
```

> Hook di `.git/hooks/` tidak ikut klon. Dalam pasukan, guna rangka kerja `pre-commit` atau `husky` supaya hook dipasang secara automatik, dan **jangan bergantung padanya semata-mata**: pembangun boleh mengelak dengan `--no-verify`. Imbasan di CI (Modul 6) ialah jaring keselamatan sebenar.

---

## Makmal 1.6: Baiki, baseline dan tindak balas

**Tujuan.** Mengeluarkan secret daripada kod, dan mengurus temuan lama dengan baseline.

### Langkah 1: keluarkan secret daripada kod

Prinsipnya: kod mengandungi **nama** konfigurasi; **nilai** datang dari luar (pemboleh ubah persekitaran, secret store).

<div class="trk trk-a" markdown="1">

```bash
sed -i -E 's/(Password=)[^;"]+/\1/; s/("Secret": ")[^"]+/\1/; s/("ApiKey": ")[^"]+/\1/' aspnet-app/appsettings.json
sed -i '/^ENV Jwt__Secret=/d' aspnet-app/Dockerfile
git diff --stat
```

ASP.NET Core membaca konfigurasi daripada pemboleh ubah persekitaran dengan `__` sebagai pemisah, jadi nilai disuap semasa jalan:

```bash
docker run -d --name kedai -p 8080:8080 \
  -e Jwt__Secret="$(openssl rand -hex 16)" \
  -e Pembayaran__ApiKey="$(openssl rand -hex 16)" \
  aspnet-app:latest
```

Untuk pembangunan tempatan tanpa Docker, guna `dotnet user-secrets` (disimpan di luar repo).

</div>

<div class="trk trk-b" markdown="1">

```bash
sed -i -E "s/env\('PAYMENT_API_KEY', '[^']*'\)/env('PAYMENT_API_KEY')/; s/('mail_password' => )'[^']*'/\1env('MAIL_PASSWORD')/; s/('db_admin_password' => )'[^']*'/\1env('DB_ADMIN_PASSWORD')/" laravel-app/config/kedai.php
sed -i '/^ENV PAYMENT_API_KEY=/d' laravel-app/Dockerfile
git diff --stat
```

Laravel membaca nilai daripada `.env` (yang diabaikan oleh git) atau pemboleh ubah persekitaran:

```bash
docker run -d --name kedai -p 8081:8080 \
  -e PAYMENT_API_KEY="$(openssl rand -hex 16)" \
  -e MAIL_PASSWORD="$(openssl rand -hex 16)" \
  -e DB_ADMIN_PASSWORD="$(openssl rand -hex 16)" \
  laravel-app:latest
```

</div>

Sahkan:

<div class="trk trk-a" markdown="1">

```bash
gitleaks dir aspnet-app --no-banner
```

</div>

<div class="trk trk-b" markdown="1">

```bash
gitleaks dir laravel-app --no-banner
```

</div>

Anda mesti melihat `no leaks found`. Hentikan kontena: `docker rm -f kedai`.

Simpan perubahan ini dalam git (hook pre-commit anda mengimbas perubahan dan akan lulus kerana tiada secret lagi):

```bash
git add -A
git commit -m "Keluarkan secret daripada kod"
```

> Jangan commit fail `alat.sh`, `gitleaks-lab.toml` dan hasil imbasan jika anda tidak mahu; `git add aspnet-app laravel-app` (hanya folder app) ialah pilihan yang lebih sempit. Perubahan ini penting: Modul 2 dan seterusnya bermula daripada keadaan ini.

### Langkah 2: sejarah masih bocor

```bash
gitleaks git . --no-banner -l error; echo "exit=$?"
```

Sejarah masih ada 15 temuan (`exit=1`), kerana commit lama tidak berubah. Anda tidak boleh menyelesaikannya dengan commit baharu.

### Langkah 3: baseline

Selepas secret lama **diputar**, anda mahu pipeline hanya gagal untuk secret **baharu**. Jana baseline daripada keadaan semasa:

```bash
gitleaks git . --no-banner -f json -r gitleaks-baseline.json -l error
gitleaks git . --no-banner --baseline-path gitleaks-baseline.json -l error; echo "exit=$?"
```

Pada langkah kedua `exit=0`: temuan dalam baseline diabaikan. Tambah secret baharu dan commit, kemudian jalankan semula arahan kedua: `exit=1`.

<div class="trk trk-a" markdown="1">

```bash
echo 'api_key = "Zq8w3kLm2Pv9Xb7Nc4Rt6Yh1"' > aspnet-app/baru.txt
git add aspnet-app/baru.txt && git commit --no-verify -qm "uji secret baharu"
gitleaks git . --no-banner --baseline-path gitleaks-baseline.json -l error; echo "exit=$?"
```

</div>

<div class="trk trk-b" markdown="1">

```bash
echo 'api_key = "Zq8w3kLm2Pv9Xb7Nc4Rt6Yh1"' > laravel-app/baru.txt
git add laravel-app/baru.txt && git commit --no-verify -qm "uji secret baharu"
gitleaks git . --no-banner --baseline-path gitleaks-baseline.json -l error; echo "exit=$?"
```

</div>

`--no-verify` melangkau hook pre-commit supaya anda dapat menguji imbasan sejarah. Buang commit ujian itu: `git reset --hard HEAD~1` (selamat kerana perubahan Langkah 1 sudah di-commit).

### Urutan apabila secret bocor

1. **Putar** (revoke dan cipta baharu) secret itu. Ini langkah yang paling penting dan paling pantas.
2. **Semak log** pembekal untuk penggunaan luar biasa sejak secret itu terbocor.
3. **Keluarkan** daripada kod dan sumber (seperti Langkah 1).
4. **Bersihkan sejarah** hanya jika perlu (`git filter-repo`), dengan faham bahawa klon dan fork lama masih mempunyainya. Ini langkah kosmetik, bukan penyelesaian.
5. **Tambah kawalan**: pre-commit, imbasan CI, baseline.

---

## Secrets management

Mengeluarkan secret daripada kod belum cukup; ia perlu disimpan dan diedarkan dengan selamat.

| Pendekatan | Sesuai untuk | Catatan |
|---|---|---|
| Pemboleh ubah persekitaran | App kontena mudah | Mudah, tetapi kelihatan dalam `docker inspect` dan proses; jangan log |
| `dotnet user-secrets`, `.env` (git-ignored) | Pembangunan tempatan | Jangan guna di produksi |
| Secret store awan (Azure Key Vault, AWS Secrets Manager) | Produksi awan | Akses melalui identiti app, bukan kunci statik |
| Kubernetes Secret | Kluster | Hanya base64, bukan penyulitan; hadkan RBAC dan sulitkan etcd |
| Sealed Secrets / SOPS | GitOps | Secret disulitkan dalam git; hanya kluster/kunci anda boleh menyahsulit |
| OIDC (identiti persekutuan) | CI/CD | Tiada secret jangka panjang; CI menukar token sementara |

Peraturan ringkas: **jangan hantar secret, hantar identiti**. Bila boleh, gantikan kunci statik dengan identiti yang dikeluarkan secara sementara.

## Senarai semak Modul 1

- [ ] Saya menjalankan `gitleaks dir` dan `gitleaks git` dan faham bezanya
- [ ] Saya melihat peraturan lalai terlepas YAML K8s, dan peraturan tersuai menangkapnya
- [ ] Saya tahu kenapa Trivy `secret` tidak menemui secret lab tetapi `trivy config` menegur Dockerfile
- [ ] Pre-commit hook saya menghalang commit yang mengandungi secret
- [ ] Saya mengeluarkan secret daripada kod dan `gitleaks dir` melaporkan `no leaks found`
- [ ] Saya boleh terangkan kenapa sejarah masih bocor dan urutan tindak balas

## Rujukan

- Gitleaks: <https://github.com/gitleaks/gitleaks>
- TruffleHog: <https://github.com/trufflesecurity/trufflehog>
- OWASP Secrets Management Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html>
