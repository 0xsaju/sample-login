#!/bin/bash
set -e

# Source environment variables
source .env

# Create regular secret
cat <<EOF > temp-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: github-pat
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
type: Opaque
stringData:
  type: git
  url: https://github.com/0xsaju/sample-login.git
  username: 0xsaju
  password: $GITHUB_PAT
EOF

# Seal the secret
kubeseal \
  --controller-namespace=kube-system \
  --scope cluster-wide \
  --format yaml \
  < temp-secret.yaml > k8s/argocd/sealed-repo-secret.yaml

# Clean up
rm temp-secret.yaml
