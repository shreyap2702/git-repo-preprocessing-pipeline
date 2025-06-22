import os
import subprocess
import shutil

def validate_url(url):
    if "https://github.com/" in url:
        parts = url.replace("https://github.com/", "").split("/")
        if len(parts) == 2 and parts[0] != "" and parts[1] != "":
            return True
        else:
            print("Please enter a valid repository URL in the format https://github.com/username/repository")
            return False
    return False

def clone_repository(github_url, output_dir):
    os.makedirs(output_dir,exist_ok=True) 
    
    repo_name_with_git_suffix = github_url.split('/')[-1]
    if repo_name_with_git_suffix.endswith('.git'):
        repo_name = repo_name_with_git_suffix[:-len('.git')]
    else:
        repo_name = repo_name_with_git_suffix
    
    cloned_repo_path = os.path.join(output_dir, repo_name) 
    
    subprocess.run(["git", "clone","--depth=1", github_url, cloned_repo_path], check=True) 
    
    return cloned_repo_path

def cleanup_repo(repo_path):
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
        
def process_repo_clone(url):
    if validate_url(url):
        target_clone_base_dir = "output/cloned_repos" 
        cloned_path = clone_repository(url, target_clone_base_dir)
        return cloned_path
    return None