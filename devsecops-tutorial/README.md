# Bengkel DevSecOps Empat Hari

Bengkel ini mengajar cara membina keselamatan ke dalam proses membina dan menghantar perisian, menggunakan dua app sebenar yang **sengaja tidak selamat**. Anda akan mencari, memahami dan membaiki vulnerability menggunakan lima jenis imbasan, kemudian menyatukan semuanya dalam pipeline.

Jurulatih: Irwan Azam Ahmad

## Apa yang anda akan capai

Selepas empat hari, anda boleh:

1. Menerangkan DevSecOps, shift-left dan quality gate, dan kenapa kontena serta kod yang dijana AI menambah risiko.
2. Membuat threat model ringkas untuk sebuah app web.
3. Menjalankan **Secret Detection** (Gitleaks), **SAST** (Semgrep), **SCA** (Trivy, `dotnet`/`composer audit`), **IaC scan** (Trivy, Checkov, hadolint, kube-linter) dan **DAST** (ZAP), serta membaca hasilnya dengan kritikal.
4. Menolak image ke **Harbor**, melihat imbasan automatik dan polisi yang menyekat image berisiko.
5. Membina pipeline CI dengan quality gate, menjana SBOM dan menandatangani image.
6. Mengeraskan (harden) deployment Kubernetes pada kluster k3d.

## Jadual

| Hari | 9:00 pagi – 1:00 petang | 2:00 – 5:00 petang |
|---|---|---|
| 1 | [Modul 0](modul-0-pengenalan/README.md): pengenalan dan threat modeling | [Modul 1](modul-1-secret/README.md): Secret Detection dan secrets management |
| 2 | [Modul 2](modul-2-sast/README.md): SAST dan kod yang dijana AI | [Modul 3](modul-3-sca/README.md): SCA, SBOM dan pakej yang direka AI |
| 3 | [Modul 4](modul-4-container-iac/README.md): container, Harbor dan IaC | [Modul 5](modul-5-dast/README.md): DAST |
| 4 | [Modul 6](modul-6-cicd/README.md): CI/CD dan supply chain | [Modul 7](modul-7-hardening/README.md): hardening K8s, capstone dan penilaian |

Rehat kira-kira 15 minit pada pertengahan setiap sesi.

## Dua trek, satu pilihan

Anda mengikut **satu** trek. Pilih di menu kiri (**Trek anda**). Kandungan trek lain disembunyikan, dan anda boleh memilih **Papar kedua-duanya** sebagai cabaran.

| Trek | App | Teknologi |
|---|---|---|
| A | `aspnet-app/` | ASP.NET Core (.NET 10), SQLite |
| B | `laravel-app/` | PHP Laravel 13, SQLite |

Kedua-dua app ialah "Kedai Bengkel" dengan fungsi yang sama dan vulnerability yang hampir sama. Latihan IaC (`k8s/`, `terraform/`) dikongsi.

## Cara guna panduan ini

- Setiap **Makmal** ada kotak **Selesai** untuk menjejak kemajuan (disimpan dalam pelayar anda).
- Blok kod ada butang **Salin**. Jalankan dalam terminal **WSL2 Ubuntu** (atau Linux/macOS) dari folder repo lab, kecuali dinyatakan.
- Bahagian **Jawapan** dilipat. Cuba dahulu sebelum membukanya.
- Fail yang dirujuk (skrip, polisi, tampalan) ada di bahagian **Fail modul** pada hujung setiap modul.

> **Amaran keselamatan.** Kedua-dua app mengandungi vulnerability sebenar. Jalankan hanya pada laptop anda dan jangan deploy ke internet. Semua kata laluan, kunci dan token dalam repo adalah **palsu** dan dijana untuk latihan. Jangan guna alat imbasan pada sistem yang bukan milik anda tanpa kebenaran bertulis.

## Peraturan makmal

1. Satu alat pada satu masa. Laptop 8 GB tidak muat menjalankan semuanya serentak.
2. Hentikan kontena selepas guna: `docker ps`, kemudian `docker rm -f <nama>`.
3. Jangan edit server Harbor atau projek peserta lain.
4. Bila buntu, tanya sebelum menghabiskan lebih 10 minit pada satu masalah.
