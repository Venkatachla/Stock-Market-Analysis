#!/usr/bin/env python3
"""
CI/CD Setup Verification Script
Validates Docker, Kubernetes, and GitHub Actions configuration
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Tuple, List

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class VerificationScript:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.deployment_dir = self.project_root / 'deployment'
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def run_command(self, cmd: str) -> Tuple[int, str]:
        """Run shell command and return exit code and output"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return 1, "Command timeout"
        except Exception as e:
            return 1, str(e)

    def check(self, name: str, condition: bool, message: str = "") -> bool:
        """Check condition and report result"""
        if condition:
            print(f"{Colors.GREEN}✓{Colors.END} {name}")
            self.passed += 1
        else:
            print(f"{Colors.RED}✗{Colors.END} {name}")
            if message:
                print(f"  {Colors.YELLOW}→{Colors.END} {message}")
            self.failed += 1
        return condition

    def file_exists(self, path: str, name: str) -> bool:
        """Check if file exists"""
        exists = Path(path).exists()
        return self.check(f"File exists: {name}", exists, f"Path: {path}")

    def directory_exists(self, path: str, name: str) -> bool:
        """Check if directory exists"""
        exists = Path(path).is_dir()
        return self.check(f"Directory exists: {name}", exists, f"Path: {path}")

    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}{text}{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    def verify_docker_files(self):
        """Verify Docker configuration files"""
        self.print_header("Docker Configuration")
        
        self.file_exists(
            str(self.project_root / '.dockerignore'),
            '.dockerignore'
        )
        
        self.file_exists(
            str(self.deployment_dir / 'docker' / 'backend' / 'Dockerfile'),
            'Backend Dockerfile'
        )
        
        self.file_exists(
            str(self.deployment_dir / 'docker' / 'frontend' / 'Dockerfile'),
            'Frontend Dockerfile'
        )
        
        self.file_exists(
            str(self.deployment_dir / 'docker' / 'frontend' / 'nginx.conf'),
            'Frontend nginx.conf'
        )

    def verify_kubernetes_files(self):
        """Verify Kubernetes manifest files"""
        self.print_header("Kubernetes Configuration")
        
        k8s_dir = self.deployment_dir / 'kubernetes'
        manifests = [
            ('configmap.yaml', 'ConfigMap'),
            ('secret.yaml', 'Secret'),
            ('backend-deployment.yaml', 'Backend Deployment'),
            ('backend-service.yaml', 'Backend Service'),
            ('frontend-deployment.yaml', 'Frontend Deployment'),
            ('frontend-service.yaml', 'Frontend Service'),
            ('ingress.yaml', 'Ingress'),
        ]
        
        for filename, name in manifests:
            self.file_exists(str(k8s_dir / filename), name)

    def verify_github_actions(self):
        """Verify GitHub Actions workflow"""
        self.print_header("GitHub Actions Workflow")
        
        workflow_file = self.project_root / '.github' / 'workflows' / 'docker-k8s-deploy.yml'
        self.file_exists(str(workflow_file), 'docker-k8s-deploy.yml')
        
        if workflow_file.exists():
            content = workflow_file.read_text()
            
            self.check(
                "Workflow triggers on push",
                'on:' in content and 'push:' in content
            )
            
            self.check(
                "Workflow includes test job",
                'test:' in content or 'Test' in content
            )
            
            self.check(
                "Workflow includes Docker build job",
                'build-and-push:' in content or 'docker/build-push-action' in content
            )
            
            self.check(
                "Workflow includes Kubernetes deploy job",
                'deploy:' in content or 'kubectl' in content
            )

    def verify_docker_installed(self):
        """Verify Docker is installed"""
        self.print_header("Local Environment")
        
        code, output = self.run_command("docker --version")
        self.check(
            "Docker installed",
            code == 0,
            "Install Docker to build images locally"
        )
        if code == 0:
            print(f"  {Colors.BLUE}→{Colors.END} {output.strip()}")

    def verify_kubectl_installed(self):
        """Verify kubectl is installed"""
        code, output = self.run_command("kubectl version --client --short")
        self.check(
            "kubectl installed",
            code == 0,
            "Install kubectl to manage Kubernetes"
        )
        if code == 0:
            print(f"  {Colors.BLUE}→{Colors.END} {output.strip()}")

    def verify_kubernetes_cluster(self):
        """Verify Kubernetes cluster connection"""
        code, output = self.run_command("kubectl cluster-info")
        connected = code == 0
        self.check(
            "Kubernetes cluster accessible",
            connected,
            "Configure kubeconfig or start cluster (minikube start)"
        )

    def verify_git_branch(self):
        """Verify git branch status"""
        self.print_header("Git Repository")
        
        code, branch = self.run_command("git rev-parse --abbrev-ref HEAD")
        
        is_devops_branch = code == 0 and 'devops/docker-k8s-cicd' in branch
        self.check(
            "On devops/docker-k8s-cicd branch",
            is_devops_branch,
            f"Current branch: {branch.strip()}"
        )

    def verify_file_content(self):
        """Verify critical file contents"""
        self.print_header("File Content Validation")
        
        # Check backend Dockerfile
        backend_dockerfile = self.deployment_dir / 'docker' / 'backend' / 'Dockerfile'
        if backend_dockerfile.exists():
            content = backend_dockerfile.read_text()
            self.check(
                "Backend Dockerfile uses Python 3.11",
                'python:3.11' in content
            )
            self.check(
                "Backend Dockerfile exposes port 8000",
                '8000' in content
            )
            self.check(
                "Backend Dockerfile includes health check",
                'HEALTHCHECK' in content
            )

        # Check frontend Dockerfile
        frontend_dockerfile = self.deployment_dir / 'docker' / 'frontend' / 'Dockerfile'
        if frontend_dockerfile.exists():
            content = frontend_dockerfile.read_text()
            self.check(
                "Frontend Dockerfile uses Node 18",
                'node:18' in content
            )
            self.check(
                "Frontend Dockerfile uses nginx",
                'nginx' in content
            )

    def verify_deployment_readiness(self):
        """Verify all deployment components"""
        self.print_header("Deployment Readiness")
        
        # Check namespace
        code, _ = self.run_command("kubectl get namespace stockpulse")
        self.check(
            "stockpulse namespace exists",
            code == 0,
            "Create with: kubectl create namespace stockpulse"
        )
        
        # Check docker registry secret
        code, _ = self.run_command("kubectl get secret dockerhub-secret -n stockpulse")
        has_secret = code == 0
        self.check(
            "Docker registry secret configured",
            has_secret,
            "Configure with: kubectl create secret docker-registry dockerhub-secret ..."
        )

    def print_summary(self):
        """Print summary statistics"""
        self.print_header("Verification Summary")
        
        total = self.passed + self.failed
        
        print(f"\n{Colors.GREEN}Passed: {self.passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
        print(f"Total checks: {total}\n")
        
        if self.failed == 0:
            print(f"{Colors.GREEN}✓ All checks passed! Setup is ready.{Colors.END}\n")
            return True
        else:
            print(f"{Colors.RED}✗ Some checks failed. Review above for details.{Colors.END}\n")
            return False

    def run_all_checks(self):
        """Run all verification checks"""
        print(f"\n{Colors.BLUE}StockPulse CI/CD Setup Verification{Colors.END}\n")
        
        self.verify_docker_files()
        self.verify_kubernetes_files()
        self.verify_github_actions()
        self.verify_docker_installed()
        self.verify_kubectl_installed()
        self.verify_kubernetes_cluster()
        self.verify_git_branch()
        self.verify_file_content()
        self.verify_deployment_readiness()
        
        success = self.print_summary()
        
        print(f"\n{Colors.BLUE}Next Steps:{Colors.END}")
        print("1. Add GitHub Secrets (DOCKER_USERNAME, DOCKER_PASSWORD, KUBE_CONFIG_DATA)")
        print("2. Commit changes: git add . && git commit -m 'add CI/CD pipeline'")
        print("3. Push to GitHub: git push origin devops/docker-k8s-cicd")
        print("4. Monitor GitHub Actions → Docker Build & Kubernetes Deploy")
        print()
        
        return 0 if success else 1

def main():
    """Main entry point"""
    try:
        verifier = VerificationScript()
        exit_code = verifier.run_all_checks()
        sys.exit(exit_code)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
