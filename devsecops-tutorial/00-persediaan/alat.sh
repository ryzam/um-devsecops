# alat.sh: fungsi shell yang menjalankan alat keselamatan melalui Docker.
# Anda tidak perlu memasang gitleaks, trivy, semgrep dan lain-lain pada laptop.
#
# Guna (dalam terminal WSL2 Ubuntu atau Linux/macOS, dari folder repo lab):
#   source alat.sh
#   gitleaks --version
#
# REG: awalan registry untuk imej alat. Biarkan kosong (Docker Hub). Instruktur boleh beri nilai
#      seperti REG=harbor.lab.test/dockerhub/ jika had tarik Docker Hub dicapai.
REG="${REG:-}"

gitleaks()   { docker run --rm -v "$PWD":/repo -w /repo -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=safe.directory -e GIT_CONFIG_VALUE_0=/repo "${REG}zricethezav/gitleaks:v8.30.1" "$@"; }
trivy()      { docker run --rm -v "$PWD":/work -w /work -v trivy-cache:/root/.cache -v /var/run/docker.sock:/var/run/docker.sock "${REG}aquasec/trivy:0.76.2" "$@"; }
semgrep()    { docker run --rm -v "$PWD":/src -w /src -e SEMGREP_SEND_METRICS=off "${REG}semgrep/semgrep:1.183.0" semgrep "$@"; }
hadolint()   { docker run --rm -i -v "$PWD":/src -w /src "${REG}hadolint/hadolint:v2.12.0" hadolint "$@"; }
checkov()    { docker run --rm -v "$PWD":/src -w /src "${REG}bridgecrew/checkov:3.4.3" "$@"; }
kube-linter(){ docker run --rm -v "$PWD":/src -w /src "${REG}stackrox/kube-linter:v0.8.3" "$@"; }
# dotnet dan composer: untuk SCA dan pengurusan pakej tanpa memasang .NET SDK atau PHP pada laptop.
dotnet()     { docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -e DOTNET_CLI_HOME=/tmp -e DOTNET_NOLOGO=1 -v "$PWD":/src -w /src "${REG}mcr.microsoft.com/dotnet/sdk:10.0" dotnet "$@"; }
composer()   { docker run --rm -u "$(id -u):$(id -g)" -e COMPOSER_HOME=/tmp -v "$PWD":/app -w /app "${REG}composer:2" "$@"; }
syft()       { docker run --rm -v "$PWD":/work -w /work -v /var/run/docker.sock:/var/run/docker.sock "${REG}anchore/syft:v1.57.0" "$@"; }
# ZAP berjalan pada rangkaian Docker "dast" supaya boleh capai app melalui nama kontena.
# Had memori 2 GB: tanpa had, imbasan penuh ZAP boleh memakai lebih 4 GB dan mematikan laptop 8 GB.
zap()        { mkdir -p zap-hasil && chmod 777 zap-hasil && docker network create dast >/dev/null 2>&1; docker run --rm --network dast --memory 2g --memory-swap 2g -v "$PWD/zap-hasil":/zap/wrk:rw "${REG}ghcr.io/zaproxy/zaproxy:2.17.0" "$@"; }

echo "alat.sh dimuatkan: gitleaks trivy semgrep hadolint checkov kube-linter zap dotnet composer syft"
