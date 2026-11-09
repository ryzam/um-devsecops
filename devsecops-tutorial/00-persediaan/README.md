# Persediaan: alat dan akses

**Sebelum Hari 1. Semua peserta.** Siapkan sekurang-kurangnya sehari sebelum bengkel kerana ada muat turun besar.

Selepas bahagian ini anda ada: terminal WSL2 dengan Docker, repo lab, alat imbasan (melalui Docker), akses ke **Harbor**, dan skrip semakan yang lulus.

<div data-fig="seni-bina-makmal"></div>

## Keperluan laptop

| Perkara | Minimum |
|---|---|
| RAM | 8 GB (had WSL2 ditetapkan di bawah) |
| Disk kosong | 30 GB (imej alat sahaja ≈ 7 GB) |
| Sistem pengendalian | Windows 10/11 dengan WSL2, atau Linux/macOS |
| Hak admin | Perlu, untuk fail `hosts` dan sijil |

## 1. WSL2 dan Docker Desktop

1. Pasang **Docker Desktop** dengan backend **WSL2**, dan pasang taburan **Ubuntu** untuk WSL2.
2. Dalam Docker Desktop: **Settings → Resources → WSL integration**, hidupkan Ubuntu.
3. Hadkan memori WSL2 supaya Windows tidak kehabisan RAM. Cipta fail `%UserProfile%\.wslconfig` (PowerShell):

```powershell
notepad $env:UserProfile\.wslconfig
```

dengan kandungan:

```ini
[wsl2]
memory=5GB
processors=4
swap=2GB
```

Kemudian mulakan semula WSL dari PowerShell:

```powershell
wsl --shutdown
```

> Semua arahan dalam panduan ini dijalankan dalam terminal **Ubuntu (WSL2)**, bukan PowerShell, kecuali ditanda **PowerShell**. Letak repo di dalam sistem fail Linux (`~/`), bukan di `/mnt/c/`, kerana jauh lebih laju.

### Masuk ke terminal Ubuntu

Dalam **PowerShell**, semak taburan WSL anda:

```powershell
wsl -l -v
```

Anda mesti melihat `Ubuntu` dengan `VERSION` **2**. Jika Ubuntu tiada, pasang (PowerShell sebagai Administrator, kemudian mulakan semula komputer dan cipta nama pengguna dan kata laluan Linux apabila diminta):

```powershell
wsl --install -d Ubuntu
```

Untuk **masuk** ke Ubuntu:

```powershell
wsl -d Ubuntu
```

Anda boleh juga membuka aplikasi **Ubuntu** dari menu Start, atau profil Ubuntu dalam Windows Terminal. Semak anda berada di tempat yang betul:

```bash
whoami
pwd
```

`whoami` mesti nama pengguna Linux anda (**bukan** `root`) dan `pwd` mesti bermula dengan `/home/`. Untuk keluar, taip `exit`.

Tiga perkara yang sering menyusahkan:

- **Jangan guna `wsl -u root`.** Folder rumah dan fail yang dijana akan menjadi milik root, dan sebahagian arahan kemudian menetapkan pemilik fail mengikut pengguna anda (`id -u`).
- **Jangan bekerja dalam `/mnt/c/...`.** Jika anda menjalankan `wsl` dari PowerShell yang berada dalam folder Windows (contohnya `C:\Users\anda\Projects`), terminal Ubuntu bermula di `/mnt/c/Users/anda/Projects`. Taip `cd ~` untuk pulang ke rumah Linux anda.
- **Jalankan semua arahan dalam satu sesi.** Memanggil `wsl -d Ubuntu <arahan>` berulang kali dari PowerShell memulakan shell baharu setiap kali, jadi fungsi seperti `source alat.sh` hilang. Masuk dahulu ke dalam Ubuntu, kemudian jalankan arahan di dalamnya.

Jika Ubuntu bukan taburan lalai dan anda mahu `wsl` sahaja memasukinya: `wsl --set-default Ubuntu`.

Sahkan dalam terminal Ubuntu:

```bash
docker version --format '{{.Server.Version}}'
docker run --rm hello-world
```

## 2. Repo lab dan bahan tutorial

Ada dua repo GitHub awam. Anda tidak memerlukan akaun GitHub untuk mengklonnya.

| Repo | Isi |
|---|---|
| `ryzam/um-devsecops-lab` | **App lab** (ASP.NET Core dan Laravel, sengaja tidak selamat), `k8s/` dan `terraform/`. Repo kerja anda sepanjang bengkel |
| `ryzam/um-devsecops` | **Tutorial** dan semua **fail modul**: `alat.sh`, `ca.crt`, tampalan, Dockerfile selamat, manifest, workflow dan pipeline |

Dalam terminal **Ubuntu (WSL)**, dari folder rumah anda (bukan `/mnt/c/`):

```bash
cd ~
git clone https://github.com/ryzam/um-devsecops-lab.git devsecops-lab
git clone https://github.com/ryzam/um-devsecops.git
```

Salin `alat.sh` (Bahagian 3) ke dalam repo lab, dan semak sejarahnya:

```bash
cp ~/um-devsecops/devsecops-tutorial/00-persediaan/alat.sh ~/devsecops-lab/
cd ~/devsecops-lab
git log --oneline | head -3
```

Isi repo lab:

| Folder atau fail | Apa itu |
|---|---|
| `aspnet-app/` | App ASP.NET Core (Trek A) |
| `laravel-app/` | App Laravel (Trek B) |
| `k8s/` | Manifest Kubernetes untuk kedua-dua app (diimbas dalam Modul 1, dibaiki dalam Modul 7) |
| `terraform/` | Contoh Terraform yang sengaja tidak selamat (diimbas dan dibaiki dalam Modul 4) |

Anda mesti melihat sekurang-kurangnya tiga commit. Repo lab mempunyai sejarah git yang sengaja mengandungi secret palsu: **jangan padamkan folder `.git`** dan jangan klon semula dengan `--depth 1`.

Semua fail yang tutorial panggil **Fail modul** (tampalan, Dockerfile, manifest, `gitlab-ci.yml` dan lain-lain) ada juga dalam `~/um-devsecops/devsecops-tutorial/modul-*/`. Anda boleh menyalinnya dengan `cp` dan tidak perlu menyalin daripada halaman web, yang mudah menambah hujung baris Windows (CRLF) dan merosakkan skrip serta tampalan.

**Mengemas kini bahan.** Jika instruktur mengumumkan pembetulan pada tutorial atau fail modul, tarik daripada repo tutorial:

```bash
cd ~/um-devsecops && git pull
```

**Jangan** jalankan `git pull` pada `~/devsecops-lab` selepas anda mula membuat perubahan: repo itu ialah kerja anda, dan perubahan anda boleh berlanggar dengan kemas kini. Jika instruktur menukar app lab, anda akan diberi arahan khusus.

> Jika `git clone` gagal dengan ralat sijil atau rangkaian, semak sambungan internet anda; GitHub menggunakan sijil awam dan tidak memerlukan CA lab. Jika anda ditanya nama pengguna dan kata laluan GitHub, URL repo salah (repo awam tidak meminta log masuk).

## 3. Alat imbasan (melalui Docker)

Anda tidak memasang gitleaks, trivy, semgrep dan lain-lain. Fail `alat.sh` (juga di bahagian **Fail modul** di bawah) mentakrif fungsi shell yang menjalankan setiap alat dalam kontena dengan versi yang dikunci. Anda sudah menyalinnya ke folder `~/devsecops-lab` dalam Bahagian 2; jika belum, salin dengan arahan di sana.

Muat turun semua imej sekarang (≈ 7 GB, ambil masa). Lakukan di rangkaian yang laju, bukan semasa bengkel:

```bash
source alat.sh
for i in zricethezav/gitleaks:v8.30.1 aquasec/trivy:0.76.2 semgrep/semgrep:1.183.0 hadolint/hadolint:v2.12.0 \
         bridgecrew/checkov:3.4.3 stackrox/kube-linter:v0.8.3 ghcr.io/zaproxy/zaproxy:2.17.0; do docker pull "$i"; done
```

Sahkan. Buka terminal Ubuntu **sebagai pengguna biasa anda** (aplikasi Ubuntu atau Windows Terminal; bukan `wsl -u root`), masuk ke folder repo, dan jalankan semua arahan dalam **satu sesi** terminal yang sama:

```bash
source alat.sh
gitleaks version
trivy --version
```

> `source alat.sh` hanya hidup dalam terminal tempat anda menjalankannya. Jika anda memanggil `wsl -d Ubuntu gitleaks version` dari PowerShell, setiap panggilan memulakan shell baharu dan fungsi `gitleaks` tidak wujud. Masuk dahulu ke dalam Ubuntu (taip `wsl -d Ubuntu`, tanpa arahan lain), kemudian jalankan arahan di atas. Jika `source alat.sh` tidak mencetak baris `alat.sh dimuatkan: ...`, fail itu tidak dimuatkan; semak bahawa ia disimpan dengan hujung baris Unix (`sed -i 's/\r$//' alat.sh`).

Pada Hari 4 anda juga memerlukan `k3d` dan `kubectl`; arahan pemasangan ada di [Modul 7](../modul-7-hardening/README.md).

### 3b. OWASP Threat Dragon (pilihan)

Untuk Makmal 0.1 bahagian B. Ia dipasang di **Windows**, bukan dalam WSL. Muat turun `Threat-Dragon-ng-Setup-2.6.2.exe` (≈ 154 MB) daripada [halaman release](https://github.com/OWASP/threat-dragon/releases), jalankan pemasang, dan pastikan aplikasi boleh dibuka. Tiada log masuk atau Docker diperlukan. Jika gagal, abaikan: bahagian B ialah pilihan dan bahagian A (jadual) sudah mencukupi.

## 4. Akses ke Harbor dan GitLab

Harbor (registry) dan GitLab (repo dan pipeline untuk Modul 6) berjalan di server Linode yang sama. Ia tidak mempunyai domain sebenar, jadi kita guna nama `harbor.lab.test` dan `gitlab.lab.test` yang dipetakan dalam fail `hosts` anda, dan sijil yang ditandatangani oleh CA lab (satu CA untuk kedua-duanya).

| Butiran | Nilai |
|---|---|
| Alamat | `192.53.174.104` |
| Harbor | `https://harbor.lab.test` (port 443) |
| GitLab | `https://gitlab.lab.test:8929` |
| Projek Harbor anda | `pesertaNN` (NN = nombor anda, 01 hingga 10) |
| Pengguna Harbor dan GitLab | `pesertaNN` |
| Kata laluan | diberi oleh instruktur (**sama** untuk Harbor dan GitLab) |
| Projek GitLab anda | `pesertaNN/devsecops-lab` (kosong, sedia untuk Modul 6) |

> Anda hanya menggunakan GitLab jika memilih **GitLab CI** pada Modul 6, tetapi sediakan akses sekarang supaya tidak terhenti pada Hari 4.

### 4a. Fail hosts (PowerShell sebagai Administrator)

```powershell
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "192.53.174.104 harbor.lab.test gitlab.lab.test"
```

Jika anda sudah menambah baris `harbor.lab.test` sebelum ini, buka fail `hosts` (Notepad sebagai Administrator) dan tambah `gitlab.lab.test` pada baris yang sama; jangan biarkan dua baris untuk IP yang sama.

Dalam terminal Ubuntu (WSL) juga, supaya `curl`, `git` dan `docker` di dalam WSL menemuinya:

```bash
echo "192.53.174.104 harbor.lab.test gitlab.lab.test" | sudo tee -a /etc/hosts
printf '[network]\ngenerateHosts = false\n' | sudo tee -a /etc/wsl.conf
```

Baris `generateHosts = false` menghalang WSL menulis semula `/etc/hosts` setiap kali ia dimulakan; ia berkuat kuasa selepas `wsl --shutdown` dari PowerShell. Untuk Linux/macOS biasa, hanya baris pertama diperlukan.

### 4b. Percayai CA lab

CA lab mesti dipercayai di **tiga tempat**: Windows (pelayar), Ubuntu/WSL (`curl`, `git`, `cosign`) dan daemon Docker Desktop. Jika salah satu terlepas, ia gagal dengan ralat sijil. Fail CA ialah `ca.crt` dalam klon `~/um-devsecops` (Bahagian 2).

**1. Salin `ca.crt` ke Windows.** Dalam terminal Ubuntu:

```bash
W=$(wslpath "$(powershell.exe -NoProfile -Command '[Environment]::GetFolderPath("MyDocuments")' | tr -d '\r')")
cp ~/um-devsecops/devsecops-tutorial/00-persediaan/ca.crt "$W/ca.crt"
```

**2. Import ke stor akar Windows** (pelayar dan Docker Desktop menggunakannya). Dalam **PowerShell Administrator**:

```powershell
Import-Certificate -FilePath "$([Environment]::GetFolderPath('MyDocuments'))\ca.crt" -CertStoreLocation Cert:\LocalMachine\Root
```

**3. Percayai dalam Ubuntu.** Dalam terminal Ubuntu:

```bash
sudo cp ~/um-devsecops/devsecops-tutorial/00-persediaan/ca.crt /usr/local/share/ca-certificates/lab-ca.crt
sudo update-ca-certificates
curl -s -o /dev/null -w "%{http_code}\n" https://harbor.lab.test/api/v2.0/health
```

Baris terakhir mesti mencetak `200`. `sudo` meminta **kata laluan Linux** anda, iaitu kata laluan yang anda tetapkan semasa memasang Ubuntu (bukan kata laluan Windows, Harbor atau GitLab). Jika anda terlupa, dalam **PowerShell** tetapkan yang baharu (gantikan `NAMA` dengan hasil `whoami` dalam Ubuntu):

```powershell
wsl -d Ubuntu -u root passwd NAMA
```

**4. Mulakan semula Docker Desktop sepenuhnya.** Docker Desktop mengambil CA daripada stor Windows apabila ia bermula; jika ia sudah berjalan sebelum langkah 2, daemonnya tidak nampak CA itu dan `docker login` gagal. Klik kanan ikon Docker di dulang dan pilih **Quit Docker Desktop**, kemudian dalam PowerShell:

```powershell
wsl --shutdown
```

Mulakan Docker Desktop semula dan tunggu sehingga enjinnya berjalan. Ini menghentikan kontena yang sedang berjalan.

Tutup semua tetingkap pelayar dan buka semula supaya sijil baharu dikenali. **Edge dan Chrome** menggunakan stor sijil Windows, jadi tiada langkah tambahan. **Firefox** menggunakan stor sijilnya sendiri: import `ca.crt` di **Settings → Privacy & Security → View Certificates → Authorities → Import**, dan tandakan *Trust this CA to identify websites*; atau gunakan Edge atau Chrome.

### 4c. Semak

Dalam terminal Ubuntu:

```bash
curl -s https://harbor.lab.test/api/v2.0/health | head -c 200; echo
docker login harbor.lab.test -u pesertaNN
curl -s -o /dev/null -w "GitLab: %{http_code}\n" https://gitlab.lab.test:8929/users/sign_in
```

> Jalankan semakan ini dan semua arahan `curl` dan `git` dalam tutorial di **terminal Ubuntu (WSL)**, bukan PowerShell. `curl.exe` dan Git for Windows (Schannel) memeriksa pembatalan sijil dan gagal dengan `CERT_TRUST_REVOCATION_STATUS_UNKNOWN` terhadap sijil CA lab, yang tidak mempunyai maklumat pembatalan. Pelayar tidak terkesan.

Anda mesti melihat `"status":"healthy"`, `Login Succeeded` dan `GitLab: 200`. Kemudian buka <https://gitlab.lab.test:8929> dalam pelayar dan log masuk sebagai `pesertaNN`; anda akan melihat projek `devsecops-lab`. Jika `GitLab` tidak menjawab 200 sedangkan Harbor berfungsi, port 8929 mungkin disekat oleh rangkaian anda: beritahu instruktur.

> **Log masuk GitLab memberi `422: The change you requested was rejected`?** Itu ralat token CSRF: pelayar menghantar borang yang tidak sepadan dengan kuki sesinya, dan kata laluan anda tidak disemak lagi. Muat semula halaman log masuk dan log masuk dengan segera (jangan guna halaman yang sudah lama terbuka), cuba **tetingkap InPrivate**, atau padam kuki untuk `gitlab.lab.test`. Gunakan **nama** `https://gitlab.lab.test:8929` (bukan alamat IP) selepas CA lab dipercayai, dan jangan campur kedua-duanya dalam pelayar yang sama. Pelayar Firefox memerlukan CA diimport dalam stornya sendiri (lihat catatan Persediaan 4b).

Jika `docker login` memberi `x509: certificate signed by unknown authority`, tentukan dahulu bahagian mana yang tidak mempercayai CA:

- **`curl ... /api/v2.0/health` dalam Ubuntu tidak memberi `200`** (ia memberi ralat sijil): Ubuntu belum mempercayai CA. Ulang langkah 3 dalam 4b.
- **`curl` memberi `200` tetapi `docker login` masih gagal**: daemon Docker Desktop belum mengambil CA daripada Windows. Ulang langkah 4 dalam 4b (**Quit Docker Desktop**, `wsl --shutdown`, mulakan semula), dan pastikan langkah 2 (import dalam PowerShell Administrator) berjaya.
- Cadangan terakhir: **Docker Desktop → Settings → Docker Engine**, tambah `"insecure-registries": ["harbor.lab.test"]`, kemudian **Apply & restart**. Ini melangkau pengesahan sijil dan hanya wajar untuk makmal ini.

### 4d. Hantar repo lab ke GitLab anda

Repo lab yang anda klon dalam Bahagian 2 masih menunjuk ke GitHub instruktur (`origin`). Repo itu **awam dan hanya boleh dibaca**: `git push` ke sana gagal dengan `Invalid username or token. Password authentication is not supported for Git operations`, kerana anda tidak ada kebenaran menulis. Repo kerja anda ialah projek `pesertaNN/devsecops-lab` di GitLab Linode. Sambungkannya sekarang, sekali sahaja.

**Langkah 1: beritahu Git siapa anda.** Tanpa ini, `git commit` gagal dengan `Author identity unknown` (nilai palsu pun boleh):

```bash
git config --global user.name "Nama Anda"
git config --global user.email "anda@contoh.com"
```

**Langkah 2: tukar remote.** Gantikan `pesertaNN` dengan nama pengguna anda (contohnya `peserta03`):

```bash
cd ~/devsecops-lab
git remote rename origin upstream
git remote add gitlab https://gitlab.lab.test:8929/pesertaNN/devsecops-lab.git
git remote -v
```

`upstream` ialah repo instruktur (hanya untuk dibaca), dan `gitlab` ialah projek anda. `git remote -v` mesti menunjukkan kedua-duanya.

**Langkah 3: tolak ke GitLab.**

```bash
git push -u gitlab main
```

Git meminta *Username* (`pesertaNN`) dan *Password* (kata laluan GitLab anda, yang sama dengan Harbor). Anda tidak nampak apa-apa ditaip semasa memasukkan kata laluan, itu biasa. Hasilnya berakhir dengan `branch 'main' set up to track 'gitlab/main'`. Selepas ini `git push` biasa (tanpa nama remote) menolak ke GitLab.

Buka <https://gitlab.lab.test:8929/pesertaNN/devsecops-lab> dalam pelayar: anda akan melihat `aspnet-app`, `laravel-app`, `k8s` dan `terraform`. Fail `alat.sh` yang anda salin tidak muncul kerana ia belum di-commit; itu tidak mengapa.

> **Ralat `SSL certificate problem`?** CA lab belum dipercayai dalam Ubuntu: ulang 4b. **`Authentication failed` atau `HTTP Basic: Access denied`?** Semak nama pengguna dan kata laluan. Jika masih gagal, log masuk di pelayar dahulu, kerana ia mungkin ralat 422 (lihat 4c). Pada kali pertama, jangan jalankan `git push` tanpa `-u gitlab main`: `main` masih mengikut `upstream` (GitHub instruktur), jadi ia akan memberi ralat `Invalid username or token` di atas.

## 5. Pilih trek

Pilih **Trek A** atau **Trek B** di menu kiri. Anda boleh menukar bila-bila masa.

## Senarai semak persediaan

- [ ] Terminal Ubuntu (WSL2) berfungsi dan `docker run --rm hello-world` berjaya
- [ ] `.wslconfig` ditetapkan dan WSL dimulakan semula
- [ ] Repo `devsecops-lab` dalam `~/devsecops-lab`, `alat.sh` disimpan
- [ ] Ketujuh-tujuh imej alat sudah ditarik
- [ ] (Pilihan) Threat Dragon dipasang di Windows
- [ ] Entri `hosts` ditambah dan CA lab dipercayai
- [ ] `docker login harbor.lab.test` berjaya dan `https://gitlab.lab.test:8929` boleh dilog masuk
- [ ] Identiti Git ditetapkan; jika guna GitLab, `git push -u gitlab main` berjaya (kod anda kelihatan di GitLab)
- [ ] Trek dipilih di menu kiri
