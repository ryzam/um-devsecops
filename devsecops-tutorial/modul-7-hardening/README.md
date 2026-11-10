# Modul 7: Hardening K8s, capstone dan penilaian

**Hari 4, 2:00 hingga 5:00 petang**

Dalam modul ini anda akan:

1. Mencipta kluster **k3d** satu node yang boleh menarik imej daripada Harbor.
2. Melihat **Pod Security Standards** menolak manifest tidak selamat, dan mengeraskan manifest dengan `securityContext`.
3. Mengawal trafik dengan **NetworkPolicy**.
4. Menguatkuasakan dasar dengan **Kyverno**: tiada `:latest`, hanya imej Harbor, dan hanya imej **bertandatangan**.
5. Menyatukan semuanya dalam **capstone** dan dinilai.

> Prasyarat: [Modul 6](../modul-6-cicd/README.md) siap: imej `:selamat` anda ada di Harbor dan **sudah ditandatangani** dengan cosign (Makmal 6.2). Fail `cosign.pub` dan `ca.crt` ada dalam folder repo.

> **Memori.** k3d satu node ≈ 0.4 GB; dengan Kyverno ≈ 1.2 GB. Hentikan semua kontena lain (`docker ps`) sebelum bermula, dan jangan jalankan ZAP serentak.

## Jadual

| Masa | Aktiviti |
|---|---|
| 2:00 – 2:20 | Teori: lapisan hardening |
| 2:20 – 2:50 | Makmal 7.1 dan 7.2: kluster, Pod Security Standards |
| 2:50 – 3:20 | Makmal 7.3: manifest yang dikeraskan |
| 3:20 – 3:30 | Rehat |
| 3:30 – 3:50 | Makmal 7.4: NetworkPolicy |
| 3:50 – 4:20 | Makmal 7.5: Kyverno |
| 4:20 – 4:50 | Makmal 7.6: capstone dan penilaian |
| 4:50 – 5:00 | Rumusan dan penutup |

---

## Teori ringkas

<div data-fig="lapisan-hardening"></div>

### Pod Security Standards (PSS)

Kubernetes mempunyai tiga tahap terbina dalam yang dikuatkuasakan oleh API server melalui label namespace:

| Tahap | Maksud |
|---|---|
| `privileged` | Tiada sekatan |
| `baseline` | Menyekat yang jelas berbahaya (privileged, hostNetwork, hostPath) |
| `restricted` | Amalan terbaik: bukan root, tiada eskalasi, capability dibuang, seccomp |

### securityContext yang penting

| Medan | Fungsi |
|---|---|
| `runAsNonRoot: true` + `runAsUser` (UID berangka) | Proses bukan root; UID berangka supaya kubelet boleh mengesahkan |
| `allowPrivilegeEscalation: false` | Proses tidak boleh mendapat keistimewaan lebih |
| `capabilities.drop: [ALL]` | Buang semua keupayaan Linux |
| `readOnlyRootFilesystem: true` | Sistem fail akar baca sahaja; tulis hanya ke volum yang dinyatakan |
| `seccompProfile: RuntimeDefault` | Sekat syscall berbahaya |
| `resources.requests/limits` | Elak satu pod menghabiskan node |
| `automountServiceAccountToken: false` | App tidak perlu kelayakan API Kubernetes |

### NetworkPolicy dan Kyverno

**NetworkPolicy** mengawal trafik antara pod. Pendekatan selamat: **tolak semua**, kemudian benarkan yang perlu. **Kyverno** ialah pengawal admission berasaskan dasar: ia menerima setiap permintaan ke API server dan menolak yang melanggar dasar, **termasuk** tandatangan imej yang tiada.

---

## Makmal 7.1: Cipta kluster k3d

**Tujuan.** Kluster tempatan yang boleh menarik imej peribadi daripada Harbor.

Pasang `k3d` dan `kubectl` (versi dikunci, disahkan dengan checksum). `kubectl` perlu hampir dengan versi server kluster (k3d lalai menggunakan Kubernetes 1.35):

```bash
cd /tmp
curl -fsSL -o k3d https://github.com/k3d-io/k3d/releases/download/v5.9.0/k3d-linux-amd64
echo "06d8f25bc3a971c4eb29e0ff08429b180402db0f4dec838c9eac427e296800a0  k3d" | sha256sum -c -
sudo install -m 0755 k3d /usr/local/bin/k3d

curl -fsSL -o kubectl https://dl.k8s.io/release/v1.35.5/bin/linux/amd64/kubectl
echo "90f75ea6ecc9ea5633262e1c0b83a40560003b30fc94a04cb099404fcef0c224  kubectl" | sha256sum -c -
sudo install -m 0755 kubectl /usr/local/bin/kubectl
cd ~/devsecops-lab
```

Simpan `registries.yaml` (**Fail modul**) dalam folder repo, kemudian cipta kluster. Ia memetakan `harbor.lab.test` ke IP Harbor, memasang CA lab ke dalam node, dan mematikan komponen yang tidak diperlukan untuk menjimatkan memori:

```bash
k3d cluster create lab --servers 1 --agents 0 --wait --timeout 240s \
  --host-alias 192.53.174.104:harbor.lab.test \
  --volume "$PWD/ca.crt:/etc/ssl/certs/lab-ca.crt@server:0" \
  --registry-config registries.yaml \
  --k3s-arg "--disable=traefik@server:*" --k3s-arg "--disable=servicelb@server:*"
kubectl get nodes
docker stats --no-stream --format "{{.Name}}: {{.MemUsage}}" k3d-lab-server-0
```

Kluster siap dalam kira-kira **30 saat** dan memakai kira-kira **0.4 GB** ketika rehat.

---

## Makmal 7.2: Pod Security Standards

**Tujuan.** Lihat apa yang berlaku bila manifest tidak selamat dihantar ke namespace yang dilindungi.

Cipta namespace `lab` dengan PSS `restricted` (**Fail modul**: `namespace-pss.yaml`), kemudian cuba manifest asal dalam `k8s/`:

<div class="trk trk-a" markdown="1">

```bash
kubectl apply -f namespace-pss.yaml
kubectl apply -f k8s/aspnet.yaml
kubectl -n lab get pods
kubectl -n lab get events --field-selector reason=FailedCreate -o custom-columns=PESAN:.message | head -3
```

</div>

<div class="trk trk-b" markdown="1">

```bash
kubectl apply -f namespace-pss.yaml
kubectl apply -f k8s/laravel.yaml
kubectl -n lab get pods
kubectl -n lab get events --field-selector reason=FailedCreate -o custom-columns=PESAN:.message | head -3
```

</div>

Anda melihat amaran semasa `apply`, **tiada pod**, dan peristiwa `FailedCreate` yang menyenaraikan setiap pelanggaran. Bersihkan: `kubectl -n lab delete deploy --all`.

<details>
<summary>Jawapan: apa yang dilanggar?</summary>

Deployment diterima oleh API server tetapi **pod ditolak** pada penciptaan, dengan mesej seperti: `violates PodSecurity "restricted:latest": host namespaces (hostNetwork=true), hostPort ..., privileged (...), allowPrivilegeEscalation != false, unrestricted capabilities ..., restricted volume types (hostPath volume "docker-sock")`, dan seterusnya. Setiap vulnerability IaC yang Trivy, Checkov dan kube-linter laporkan dalam Modul 4 juga disekat di sini, **pada masa jalan**, walaupun tiada sesiapa membaca laporan imbasan. Itu nilai lapisan admission.
</details>

---

## Makmal 7.3: Manifest yang dikeraskan

**Tujuan.** Menggantikan manifest dengan versi yang lulus PSS `restricted`, dan mengesahkan app masih berfungsi.

Simpan manifest yang dikeraskan dari bahagian **Fail modul** (`aspnet-selamat.yaml` atau `laravel-selamat.yaml`). Baca dan kenal pasti setiap medan `securityContext` yang dibincangkan di atas. Perhatikan juga:

- imej `harbor.lab.test/PESERTA/...:selamat` (tag tetap, bukan `:latest`);
- secret **tidak** ada dalam manifest: ia dirujuk melalui `secretKeyRef`;
- sistem fail akar baca sahaja, dengan volum `emptyDir` untuk apa yang app perlu tulis;
- `Service` jenis `ClusterIP`, bukan `NodePort`.

Cipta secret dan namespace, kemudian pasang. Ganti `peserta03` dengan nombor anda dan `KATA_LALUAN` dengan kata laluan Harbor anda:

<div class="trk trk-a" markdown="1">

```bash
P=peserta03
kubectl -n lab create secret docker-registry harbor --docker-server=harbor.lab.test \
  --docker-username=$P --docker-password='KATA_LALUAN'
kubectl -n lab create secret generic aspnet-rahsia --from-literal=Jwt__Secret="$(openssl rand -hex 16)"
sed "s/PESERTA/$P/g" aspnet-selamat.yaml | kubectl apply -f -
kubectl -n lab rollout status deploy/aspnet-app --timeout=120s
```

</div>

<div class="trk trk-b" markdown="1">

```bash
P=peserta03
kubectl -n lab create secret docker-registry harbor --docker-server=harbor.lab.test \
  --docker-username=$P --docker-password='KATA_LALUAN'
kubectl -n lab create secret generic laravel-rahsia --from-literal=PAYMENT_API_KEY="$(openssl rand -hex 16)"
sed "s/PESERTA/$P/g" laravel-selamat.yaml | kubectl apply -f -
kubectl -n lab rollout status deploy/laravel-app --timeout=150s
```

</div>

Ujian:

<div class="trk trk-a" markdown="1">

```bash
kubectl -n lab port-forward svc/aspnet-app 8095:80 &
sleep 3
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8095/
curl -s "http://localhost:8095/search?q=laptop" | grep -oE "Laptop[^<]*"
curl -s "http://localhost:8095/ping?host=127.0.0.1" | grep -oE "bytes from|Operation not permitted"
kubectl -n lab exec deploy/aspnet-app -- id
kubectl -n lab exec deploy/aspnet-app -- sh -c 'touch /app/uji; touch /data/uji && echo data-boleh-tulis'
kill %1
```

</div>

<div class="trk trk-b" markdown="1">

```bash
kubectl -n lab port-forward svc/laravel-app 8096:80 &
sleep 3
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8096/up
curl -s "http://localhost:8096/search?q=laptop" | grep -oE "Laptop[^<]*"
curl -s "http://localhost:8096/ping?host=127.0.0.1" | grep -oE "bytes from|Operation not permitted"
kubectl -n lab exec deploy/laravel-app -- id
kubectl -n lab exec deploy/laravel-app -- sh -c 'touch /app/uji; touch /data/uji && echo data-boleh-tulis'
kill %1
```

</div>

Imbas manifest baharu dengan tiga alat dan bandingkan dengan manifest asal (21 temuan Trivy/Checkov, 9 hingga 10 kube-linter):

```bash
mkdir -p /tmp/k8s-selamat && cp aspnet-selamat.yaml laravel-selamat.yaml /tmp/k8s-selamat/
trivy config /tmp/k8s-selamat
checkov -d /tmp/k8s-selamat --framework kubernetes --compact --quiet
kube-linter lint /tmp/k8s-selamat
```

<details>
<summary>Jawapan jangkaan</summary>

<div class="trk trk-a" markdown="1">

App berjalan sebagai UID `10001` (bukan root). Menulis ke `/app` gagal dengan `Read-only file system`, menulis ke `/data` berjaya. `GET /` dan `/search` berfungsi, tetapi **`/ping` tidak lagi berfungsi** (`Operation not permitted`): `ping` memerlukan keupayaan `NET_RAW` yang kita buang. Inilah harga hardening yang sebenar; pemilik app mesti memutuskan sama ada menyingkirkan ciri itu atau menggantikan dengan pendekatan yang tidak memerlukan keistimewaan.

</div>

<div class="trk trk-b" markdown="1">

App berjalan sebagai UID `10001`. Menulis ke `/app` gagal (`Read-only file system`), menulis ke `/data` berjaya. `/up`, carian dan `ping` berfungsi (imej Alpine menggunakan soket ICMP tanpa keistimewaan).

</div>

Hasil imbasan manifest yang dikeraskan: **Trivy** hanya 1 temuan Medium (`KSV-0125`: imej bukan daripada registry yang dipercayai; Kyverno mengendalikannya dalam Makmal 7.5), **kube-linter** tiada ralat, dan **Checkov** 4 baki (`CKV2_K8S_6` tiada NetworkPolicy: Makmal 7.4; `CKV_K8S_15` `imagePullPolicy`; `CKV_K8S_35` secret melalui env berbanding fail; `CKV_K8S_43` imej tanpa digest). Itu keputusan reka bentuk untuk ditimbang, bukan semua perlu dituruti.
</details>

Letakkan manifest yang dikeraskan ke dalam repo supaya pipeline (Modul 6) lulus:

<div class="trk trk-a" markdown="1">

```bash
cp aspnet-selamat.yaml k8s/aspnet.yaml
```

</div>

<div class="trk trk-b" markdown="1">

```bash
cp laravel-selamat.yaml k8s/laravel.yaml
```

</div>

> Fail `k8s/` yang satu lagi (trek lain) masih tidak selamat, dan pipeline mengimbas seluruh `k8s/`. Anda boleh membaikinya sebagai cabaran, atau edit `keselamatan.yml` supaya hanya mengimbas fail trek anda.

---

## Makmal 7.4: NetworkPolicy

**Tujuan.** Hanya klien yang dibenarkan boleh mencapai app.

Simpan `networkpolicy.yaml` (**Fail modul**). Ia tolak semua trafik masuk dalam namespace `lab`, kemudian benarkan trafik ke app hanya daripada namespace berlabel `akses=dibenarkan`. Ganti `APP` dengan `aspnet-app` atau `laravel-app`.

Cipta dua klien, satu dalam namespace dibenarkan dan satu tidak:

```bash
kubectl create ns klien; kubectl create ns asing
kubectl label ns klien akses=dibenarkan
for n in klien asing; do kubectl -n $n run klien --image=curlimages/curl --restart=Never --command -- sleep 3600; done
kubectl -n klien wait --for=condition=Ready pod/klien --timeout=90s
kubectl -n asing wait --for=condition=Ready pod/klien --timeout=90s
```

Uji **sebelum** dan **selepas** polisi (ganti `aspnet-app` jika Trek B):

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
uji() { for n in klien asing; do echo -n "dari ns $n: "; kubectl -n $n exec klien -- curl -s -m 5 -o /dev/null -w "%{http_code}\n" http://$APP.lab.svc/ 2>&1 | tail -1; done; }
echo "## tanpa polisi"; uji
sed "s/app: APP/app: $APP/" networkpolicy.yaml | kubectl apply -f -
sleep 3
echo "## dengan polisi"; uji
```

<details>
<summary>Jawapan jangkaan</summary>

Tanpa polisi: **200** daripada kedua-dua namespace. Dengan polisi: `klien` masih **200**, manakala `asing` gagal (`command terminated with exit code 7`: sambungan tidak dapat dibuat). Pertahanan berlapis: walaupun penyerang masuk ke pod lain dalam kluster, trafik ke app disekat melainkan daripada sumber yang dibenarkan.
</details>

---

## Makmal 7.5: Kyverno

**Tujuan.** Menguatkuasakan dasar supply chain pada admission.

Pasang Kyverno (versi dikunci):

```bash
kubectl apply --server-side -f https://github.com/kyverno/kyverno/releases/download/v1.19.2/install.yaml
kubectl -n kyverno wait --for=condition=Available deploy --all --timeout=240s
```

Pasang dasar tag dan registry (`kyverno-polisi.yaml`, **Fail modul**), dan uji:

```bash
kubectl apply -f kyverno-polisi.yaml
kubectl -n klien run nginx-uji --image=nginx:latest --restart=Never
kubectl -n klien run nginx-uji2 --image=nginx:1.27 --restart=Never
```

Kedua-duanya mesti **ditolak**. Baca mesej: ia menyebut dasar dan peraturan yang dilanggar.

Kini dasar tandatangan. Skrip `kyverno-tandatangan.sh` (**Fail modul**) menyediakan Kyverno untuk menghubungi Harbor (CA lab, alias hos dan kelayakan) dan memasang dasar yang **menolak imej Harbor tanpa tandatangan cosign** anda:

```bash
chmod +x kyverno-tandatangan.sh
P=peserta03 PW='KATA_LALUAN' ./kyverno-tandatangan.sh
```

Uji dengan imej bertandatangan dan imej tanpa tandatangan (daripada Makmal 6.2). Ganti `APP`:

```bash
kubectl -n klien create secret docker-registry harbor --docker-server=harbor.lab.test \
  --docker-username=$P --docker-password='KATA_LALUAN'
PULL='{"spec":{"imagePullSecrets":[{"name":"harbor"}]}}'
kubectl -n klien run sah --image=harbor.lab.test/$P/$APP:selamat --restart=Never --overrides="$PULL"
kubectl -n klien run belum-sah --image=harbor.lab.test/$P/$APP:belum-sah --restart=Never --overrides="$PULL"
```

<details>
<summary>Jawapan</summary>

Pod `sah` **dicipta**: Kyverno mengesahkan tandatangan dengan kunci awam anda dan menggantikan tag dengan digest (`mutateDigest`), jadi pod berjalan dengan imej tepat yang ditandatangani. Pod `belum-sah` **ditolak** dengan `no signatures found`.

Perhatikan satu pengajaran: ini hanya berjaya kerana imej `:selamat` anda **sudah ditandatangani** dalam Modul 6 dan kerana Harbor boleh dihubungi daripada Kyverno. Jika imej baharu tidak ditandatangani oleh pipeline, ia tidak akan berjalan di kluster. Itulah niat dasar ini: **tiada bukti, tiada jalan**.
</details>

> Dasar Kyverno dalam bengkel ini menggunakan `ClusterPolicy`, yang kini ditandakan sebagai usang dalam Kyverno 1.19 (amaran dipaparkan semasa `apply`); ia masih berfungsi dan jenis dasar baharu (`ValidatingPolicy`, `ImageValidatingPolicy`) mengganti nanti.

---

## Makmal 7.6: Capstone dan penilaian

**Tujuan.** Menunjukkan bahawa anda boleh membawa app daripada keadaan asal kepada keadaan yang boleh dipertahankan, dengan bukti.

**Tugasan.** Untuk app trek anda, tunjukkan **setiap** kriteria di bawah dengan **bukti** (arahan dan outputnya, atau tangkapan skrin tab Actions). Anda ada kira-kira 30 minit untuk membaiki apa yang masih tertinggal dan membuat demo ringkas 3 minit kepada instruktur.

| # | Kriteria | Bukti | Markah |
|---|---|---|---|
| 1 | **Secret**: tiada secret dalam kod semasa; secret lama dalam baseline | `gitleaks dir <app>` bersih; `gitleaks git . --baseline-path gitleaks-baseline.json` exit 0 | 10 |
| 2 | **SAST**: SQL/command injection dibaiki dan disahkan dengan ujian fungsi; baki Semgrep diterima dengan alasan | Imbasan Semgrep tiada ERROR; ujian `curl` | 15 |
| 3 | **SCA**: pakej dinaikkan; baki diterima dengan tarikh luput | `trivy fs --severity HIGH,CRITICAL --exit-code 1` exit 0 | 10 |
| 4 | **Imej**: Dockerfile selamat (multi-stage, bukan root, tiada secret) | `hadolint`/`trivy config`/Checkov bersih untuk Dockerfile; `docker exec ... id` bukan root | 10 |
| 5 | **Harbor**: imej ditolak, diimbas, dan ditandatangani | Skrin Harbor; `cosign verify` berjaya | 10 |
| 6 | **DAST**: tiada isyarat Tinggi selepas imbasan semula | `ringkas-zap.py` menunjukkan tinggi 0 | 15 |
| 7 | **K8s**: manifest lulus PSS `restricted`; NetworkPolicy; Kyverno menolak imej tidak bertandatangan | Pod berjalan dalam namespace `lab`; ujian polisi | 15 |
| 8 | **Pipeline**: `imbas` dan `imej` hijau; pintu terbukti menggagalkan | Tab Actions hijau; bukti larian merah dengan secret ujian | 15 |

**Jumlah 100 markah.** Skala: **90 hingga 100** cemerlang, **70 hingga 89** lulus dengan baik, **50 hingga 69** lulus, **di bawah 50** perlu mengulang bahagian tertentu.

**Soalan refleksi** (jawab ringkas semasa demo):

1. Dari semua alat hari ini, mana yang paling menemui vulnerability **sebenar** dan mana yang paling banyak **bunyi**?
2. Vulnerability mana yang **tiada alat** menemuinya, dan bagaimana anda akan menanganinya?
3. Jika anda hanya boleh menghidupkan **tiga** pintu dalam pipeline pasukan anda esok, yang mana, dan kenapa?
4. Apa yang anda akan **ukur** untuk tahu keselamatan pasukan anda bertambah baik (cadangan: masa untuk membaiki, bilangan temuan yang terbuka, liputan imbasan)?

---

## Rumusan: alat mana menangkap apa

Gunakan alat ini untuk melihat, bagi setiap vulnerability yang ditanam, **alat mana menangkapnya dan mana terlepas**. Semuanya daripada ujian sebenar yang anda jalankan dalam bengkel ini:

<div data-widget="alat"></div>

Tiga pengajaran utama bengkel:

1. **Berlapis, bukan satu alat.** Setiap alat mempunyai titik buta; liputan datang daripada gabungan.
2. **Bukti, bukan andaian.** Sahkan pembaikan dengan ujian fungsi, sahkan pintu menggagalkan, sahkan kawalan benar-benar menyekat.
3. **Konteks menentukan keutamaan.** Keterukan alat ialah titik permulaan, bukan keputusan. Threat model memberi anda bahasa untuk menilai.

## Bersihkan

```bash
k3d cluster delete lab
docker network rm dast 2>/dev/null
docker system prune -f
```

## Senarai semak Modul 7

- [ ] Kluster k3d berjalan dan boleh menarik imej daripada Harbor
- [ ] Saya melihat PSS menolak manifest asal dan faham mesej
- [ ] Manifest yang dikeraskan berjalan; saya tahu kenapa `/ping` gagal pada Trek A
- [ ] NetworkPolicy menyekat klien yang tidak dibenarkan
- [ ] Kyverno menolak `:latest`, imej bukan Harbor, dan imej tanpa tandatangan
- [ ] Saya menyiapkan capstone dan melakukan demo

## Rujukan

- Pod Security Standards: <https://kubernetes.io/docs/concepts/security/pod-security-standards/>
- Kyverno: <https://kyverno.io/docs/>
- NetworkPolicy: <https://kubernetes.io/docs/concepts/services-networking/network-policies/>
- CIS Kubernetes Benchmark: <https://www.cisecurity.org/benchmark/kubernetes>
- OWASP DevSecOps Maturity Model: <https://owasp.org/www-project-devsecops-maturity-model/>
