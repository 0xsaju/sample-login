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
data:
  url: $(echo -n "https://github.com/0xsaju/sample-login.git" | base64)
  username: $(echo -n "0xsaju" | base64)
  password: $(echo -n "$GITHUB_PAT" | base64)
  type: $(echo -n "git" | base64)
EOF

# Create sealed secret
kubeseal \
  --controller-namespace=kube-system \
  --format yaml \
  --cert-file <(kubectl get secret -n kube-system -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml) \
  < temp-secret.yaml > k8s/argocd/sealed-repo-secret.yaml

# Clean up
rm temp-secret.yaml
