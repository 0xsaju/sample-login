from diagrams import Diagram, Cluster
from diagrams.k8s.compute import Pod
from diagrams.k8s.network import Ingress, Service
from diagrams.k8s.infra import Node
from diagrams.onprem.container import Docker
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.gitops import ArgoCD
from diagrams.onprem.vcs import Github
from diagrams.onprem.client import Users

with Diagram("Sample Login Application Architecture", show=True, direction="TB"):
    # External Services
    user = Users("End Users")
    github = Github("GitHub Repo")
    dockerhub = Docker("Docker Hub")

    # CI/CD Pipeline
    with Cluster("CI/CD Pipeline"):
        github_actions = GithubActions("GitHub Actions")
        argocd = ArgoCD("ArgoCD")

    # K3s Cluster
    with Cluster("K3s Cluster"):
        with Cluster("Application Stack"):
            ingress = Ingress("Nginx Ingress")
            app_svc = Service("App Service")
            app_pods = [Pod("Flask App 1"), Pod("Flask App 2")]

    # Application Flow
    user >> ingress >> app_svc >> app_pods

    # CI/CD Flow
    github >> github_actions >> dockerhub
    dockerhub >> argocd >> app_pods
