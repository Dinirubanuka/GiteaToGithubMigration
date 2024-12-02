import requests
import os
import subprocess

# Gitea Configuration
GITEA_URL = "https://repository.entgra.net"
GITEA_TOKEN = ""  # Your Gitea personal access token
GITEA_OWNER = "proprietary"  # Owner/organization of the Gitea repositories

# GitHub Configuration
GITHUB_URL = "https://api.github.com"
GITHUB_TOKEN = ""  # Your GitHub personal access token
GITHUB_ORG = "EntgraTest"  # Your GitHub organization
GITHUB_USER = "Dinirubanuka"  # GitHub username for authentication

# Headers for API requests
gitea_headers = {"Authorization": f"token {GITEA_TOKEN}"}
github_headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

def create_github_repo(repo_name):
    print(f"Creating repository '{repo_name}' in GitHub organization...")
    github_repo_url = f"{GITHUB_URL}/orgs/{GITHUB_ORG}/repos"
    data = {
        "name": repo_name,
        "private": True,  # Set to False if you want public repos
    }
    response = requests.post(github_repo_url, headers=github_headers, json=data)
    if response.status_code == 201:
        print(f"GitHub repository '{repo_name}' created successfully!")
    elif response.status_code == 422:  # Repo already exists
        print(f"GitHub repository '{repo_name}' already exists, skipping creation.")
    else:
        print(f"Failed to create GitHub repository '{repo_name}': {response.status_code}, {response.text}")

def remove_hidden_refs(local_repo_dir):
    print(f"Removing hidden refs in the local repository '{local_repo_dir}'...")
    os.system(f"cd {local_repo_dir} && git for-each-ref --format '%(refname)' refs/pull | xargs -n 1 git update-ref -d")

def migrate_repository(gitea_repo_name):
    clone_url = f"{GITEA_URL}/{GITEA_OWNER}/{gitea_repo_name}.git"
    local_repo_dir = f"{gitea_repo_name}_clone"
    if os.path.exists(local_repo_dir):
        print(f"Directory '{local_repo_dir}' already exists, removing it...")
        os.system(f"rm -rf {local_repo_dir}")

    print(f"Cloning repository '{gitea_repo_name}' from Gitea...")
    clone_result = os.system(f"git clone --mirror {clone_url} {local_repo_dir}")
    if clone_result != 0:
        print(f"Failed to clone repository '{gitea_repo_name}' from Gitea.")
        return

    remove_hidden_refs(local_repo_dir)

    github_repo_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_ORG}/{gitea_repo_name}.git"

    print(f"Pushing repository '{gitea_repo_name}' to GitHub...")
    push_result = os.system(f"cd {local_repo_dir} && git push --mirror {github_repo_url}")
    if push_result != 0:
        print(f"Failed to push repository '{gitea_repo_name}' to GitHub.")
        return

    print(f"Repository '{gitea_repo_name}' migrated successfully, including all branches and tags.")

if __name__ == "__main__":
    gitea_repos = input("Enter Gitea repository names (comma-separated): ").strip().split(',')

    for gitea_repo_name in gitea_repos:
        gitea_repo_name = gitea_repo_name.strip()
        if gitea_repo_name:
            print(f"\nProcessing repository: {gitea_repo_name}")
            create_github_repo(gitea_repo_name)  
            migrate_repository(gitea_repo_name) 