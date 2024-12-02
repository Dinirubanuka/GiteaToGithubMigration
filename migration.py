import requests
import os

# Gitea Configuration
GITEA_URL = "https://repository.entgra.net" 
GITEA_TOKEN = "" 
GITEA_OWNER = "" 
GITEA_REPO = "" 

# GitHub Configuration
GITHUB_URL = "https://api.github.com" 
GITHUB_TOKEN = "" 
GITHUB_ORG = ""  # Your GitHub organization
GITHUB_REPO = ""  # New repo name
GITHUB_USER = ""  # GitHub username for authentication

# Headers for API requests
gitea_headers = {"Authorization": f"token {GITEA_TOKEN}"}
github_headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

def create_github_repo():
    print("Creating repository in GitHub organization...")
    github_repo_url = f"{GITHUB_URL}/orgs/{GITHUB_ORG}/repos"
    data = {
        "name": GITHUB_REPO,
        "private": True,  # Set to False if you want a public repo
    }
    response = requests.post(github_repo_url, headers=github_headers, json=data)
    if response.status_code == 201:
        print(f"GitHub repository '{GITHUB_REPO}' created successfully!")
    else:
        print(f"Failed to create GitHub repository: {response.status_code}, {response.text}")

def migrate_repository():
    # Clone the Gitea repository to a local directory
    clone_url = f"{GITEA_URL}/{GITEA_OWNER}/{GITEA_REPO}.git" 
    local_repo_dir = f"{GITEA_REPO}_clone"
    os.system(f"git clone --bare {clone_url} {local_repo_dir}")

    # Prepare GitHub repository URL for pushing
    github_repo_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_ORG}/{GITHUB_REPO}.git" 

    print("Pushing repository to GitHub...")
    os.system(f"cd {local_repo_dir} && git push --mirror {github_repo_url}")

    # Fetch and migrate tags
    print("Migrating tags from Gitea to GitHub...")
    os.system(f"cd {local_repo_dir} && git fetch --tags")
    os.system(f"cd {local_repo_dir} && git push {github_repo_url} --tags")

    print("Transferring pull requests from Gitea to GitHub...")

    # Step 1: Fetch Pull Requests from Gitea
    gitea_pr_url = f"{GITEA_URL}/api/v1/repos/{GITEA_OWNER}/{GITEA_REPO}/pulls"
    response = requests.get(gitea_pr_url, headers=gitea_headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch PRs from Gitea: {response.status_code}, {response.text}")
        return

    gitea_prs = response.json()

    for pr in gitea_prs:
        pr_title = pr['title']
        pr_body = pr['body']
        pr_state = "open" if pr["state"] == "open" else "closed"
        base_branch = pr['base']['ref']
        source_branch = pr['head']['ref']

        # Step 2: Create a Branch in GitHub for the PR
        print(f"Creating branch '{source_branch}' for PR '{pr_title}'...")
        github_branch_url = f"{GITHUB_URL}/repos/{GITHUB_ORG}/{GITHUB_REPO}/git/refs"
        source_sha = pr['head']['sha']

        branch_data = {
            "ref": f"refs/heads/{source_branch}",
            "sha": source_sha
        }

        branch_response = requests.post(github_branch_url, headers=github_headers, json=branch_data)
        if branch_response.status_code != 201:
            print(f"Failed to create branch '{source_branch}': {branch_response.status_code}, {branch_response.text}")
            continue

        # Step 3: Create a Pull Request in GitHub
        print(f"Creating pull request '{pr_title}'...")
        github_pr_url = f"{GITHUB_URL}/repos/{GITHUB_ORG}/{GITHUB_REPO}/pulls"
        pr_data = {
            "title": pr_title,
            "body": pr_body,
            "head": source_branch,
            "base": base_branch
        }

        pr_response = requests.post(github_pr_url, headers=github_headers, json=pr_data)
        if pr_response.status_code == 201:
            print(f"Pull Request '{pr_title}' migrated successfully!")
        else:
            print(f"Failed to migrate Pull Request '{pr_title}': {pr_response.status_code}, {pr_response.text}")

if __name__ == "__main__":
    create_github_repo()  # Create the GitHub repository under the organization
    migrate_repository()  # Migrate the repository from Gitea to GitHub
