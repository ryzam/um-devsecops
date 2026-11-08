#!/usr/bin/env bash
# Sediakan Kyverno untuk mengesahkan tandatangan cosign imej daripada Harbor lab, kemudian
# pasang dasar yang menolak imej Harbor yang tidak ditandatangani.
#
# Guna (dari folder repo; perlu cosign.pub, ca.crt dan kubectl yang menunjuk ke kluster k3d):
#   P=peserta03 PW='kata-laluan-harbor' ./kyverno-tandatangan.sh
#
# Ia melakukan:
#   1. ConfigMap lab-ca (ca.crt) dalam namespace kyverno
#   2. Menampal kyverno-admission-controller: hostAliases ke Harbor, CA dipercayai (SSL_CERT_FILE)
#   3. Secret kelayakan Harbor untuk Kyverno (kerana projek anda peribadi)
#   4. ClusterPolicy "imej-bertandatangan" dengan kunci awam anda
# Boleh dijalankan semula (idempotent).
set -euo pipefail

: "${P:?Tetapkan P (cth peserta03)}"
: "${PW:?Tetapkan PW (kata laluan Harbor anda)}"
HARBOR_IP="${HARBOR_IP:-192.53.174.104}"
[ -f cosign.pub ] || { echo "cosign.pub tiada dalam folder ini" >&2; exit 1; }
[ -f ca.crt ] || { echo "ca.crt tiada dalam folder ini" >&2; exit 1; }

kubectl -n kyverno create configmap lab-ca --from-file=ca.crt=ca.crt --dry-run=client -o yaml | kubectl apply -f -

kubectl -n kyverno patch deploy kyverno-admission-controller --type=strategic -p "{
  \"spec\":{\"template\":{\"spec\":{
    \"hostAliases\":[{\"ip\":\"$HARBOR_IP\",\"hostnames\":[\"harbor.lab.test\"]}],
    \"volumes\":[{\"name\":\"lab-ca\",\"configMap\":{\"name\":\"lab-ca\"}}],
    \"containers\":[{\"name\":\"kyverno\",
      \"volumeMounts\":[{\"name\":\"lab-ca\",\"mountPath\":\"/etc/lab-ca\"}],
      \"env\":[{\"name\":\"SSL_CERT_FILE\",\"value\":\"/etc/lab-ca/ca.crt\"}]}]
  }}}}"
kubectl -n kyverno rollout status deploy/kyverno-admission-controller --timeout=180s

kubectl -n kyverno create secret docker-registry harbor-kyverno --docker-server=harbor.lab.test \
  --docker-username="$P" --docker-password="$PW" --dry-run=client -o yaml | kubectl apply -f -

PUB="$(sed 's/^/                      /' cosign.pub)"
cat <<EOF | kubectl apply -f -
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: imej-bertandatangan
spec:
  validationFailureAction: Enforce
  webhookTimeoutSeconds: 30
  rules:
    - name: sahkan-cosign
      match:
        any:
          - resources:
              kinds: ["Pod"]
      verifyImages:
        - imageReferences: ["harbor.lab.test/*"]
          mutateDigest: true
          verifyDigest: true
          required: true
          imageRegistryCredentials:
            secrets:
              - harbor-kyverno
          attestors:
            - entries:
                - keys:
                    publicKeys: |-
$PUB
                    rekor:
                      ignoreTlog: true
                    ctlog:
                      ignoreSCT: true
EOF
echo "Dasar imej-bertandatangan dipasang."
