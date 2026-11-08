# um-devsecops

Bahan tutorial **Bengkel DevSecOps 4 hari** (Bahasa Melayu): Secret Detection, SAST, SCA, IaC, DAST, CI/CD dan hardening Kubernetes, untuk app ASP.NET Core dan Laravel.

## Apa yang ada dalam repo ini

| Folder | Isi |
|---|---|
| `devsecops-tutorial-html/index.html` | Tutorial interaktif (satu fail HTML). Buka dalam pelayar |
| `devsecops-tutorial/` | Sumber tutorial (Markdown) dan **fail modul**: `alat.sh`, `ca.crt`, tampalan, Dockerfile selamat, manifest K8s, workflow GitHub Actions dan pipeline GitLab CI |

App lab yang sengaja tidak selamat berada dalam repo **berasingan**: [`um-devsecops-lab`](https://github.com/ryzam/um-devsecops-lab). Ia perlu repo tersendiri kerana sejarah gitnya sengaja mengandungi secret palsu untuk latihan Secret Detection.

## Untuk peserta

Ikut bahagian **Persediaan** dalam tutorial. Ringkasnya, dalam terminal Ubuntu (WSL2):

```bash
cd ~
git clone https://github.com/ryzam/um-devsecops-lab.git devsecops-lab
git clone https://github.com/ryzam/um-devsecops.git
cp ~/um-devsecops/devsecops-tutorial/00-persediaan/alat.sh ~/devsecops-lab/
```

Untuk mengemas kini bahan tutorial: `cd ~/um-devsecops && git pull`. Jangan `git pull` pada repo lab selepas anda mula membuat perubahan.

## Amaran

App dalam `um-devsecops-lab` mengandungi kelemahan yang **disengajakan**. Jangan jalankannya pada rangkaian awam atau gunakan kodnya dalam projek sebenar. Semua secret di dalamnya palsu.

Rujuk `devsecops-tutorial-html/CARA-BINA.md` untuk membina semula tutorial HTML daripada sumber Markdown.
