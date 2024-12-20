#!/bin/bash
set -e

# Source environment variables
source .env

# Base64 encode the PAT
GITHUB_PAT_B64=$(echo -n "$GITHUB_PAT" | base64)

# Replace in template and create temporary file
sed "s/\${GITHUB_PAT}/$GITHUB_PAT_B64/" k8s/argocd/repo-secret.yaml > temp-secret.yaml

# Create sealed secret
kubeseal \
  --controller-namespace=kube-system \
  --controller-name=sealed-secrets-controller \
  --format yaml \
  < temp-secret.yaml > k8s/argocd/sealed-repo-secret.yaml

# Clean up
rm temp-secret.yaml
