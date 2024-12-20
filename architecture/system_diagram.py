from diagrams import Diagram, Cluster, Edge
from diagrams.k8s.compute import Pod, StatefulSet
from diagrams.k8s.network import Ingress, Service
from diagrams.k8s.infra import Node
from diagrams.onprem.network import Nginx
from diagrams.onprem.database import MySQL
from diagrams.onprem.compute import Server
from diagrams.programming.framework import Flask
from diagrams.onprem.container import Docker
from diagrams.onprem.ci import GithubActions  # Updated import
from diagrams.onprem.gitops import ArgoCD    # Updated import
from diagrams.onprem.vcs import Github
from diagrams.onprem.client import Users

with Diagram("Sample Login Application Architecture", show=True, direction="TB"):
    # User and external services
    user = Users("End Users")
    github = Github("GitHub Repo")
    dockerhub = Docker("Docker Hub")

    # CI/CD Pipeline
    with Cluster("CI/CD Pipeline"):
        github_actions = GithubActions("GitHub Actions")
        argocd = ArgoCD("ArgoCD")

    # K3s Cluster
    with Cluster("K3s Cluster"):
        # Master Node
        with Cluster("Master Node"):
            master = Node("K3s Master")
            
        # Worker Nodes
        with Cluster("Worker Nodes"):
            workers = [Node("Worker1"), Node("Worker2")]
            
            # Application Components
            with Cluster("Application Stack"):
                ingress = Ingress("Nginx Ingress")
                app_svc = Service("App Service")
                
                with Cluster("App Pods"):
                    app_pods = [Pod("Flask App 1"), Pod("Flask App 2")]
                
                with Cluster("Database"):
                    db_svc = Service("DB Service")
                    mysql = StatefulSet("MySQL")

    # Flow Definition
    user >> ingress
    ingress >> app_svc
    app_svc >> app_pods
    
    for pod in app_pods:
        pod >> db_svc
    
    db_svc >> mysql

    # CI/CD Flow
    github >> github_actions
    github_actions >> dockerhub
    github_actions >> github
    github << argocd
    argocd >> app_pods
