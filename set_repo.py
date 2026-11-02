import json
import subprocess
import sys
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).parent / "serpentdevflowconfig.yaml"


def load_config():
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)


def get_folder_name(repo_dir):
    return Path(repo_dir).name


def run_git(repo_dir, *args):
    result = subprocess.run(
        list(args),
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_current_origin(repo_dir):
    return run_git(repo_dir, "git", "remote", "get-url", "origin")


def find_gitea_origin(gitea_origins, folder_name):
    for origin in gitea_origins:
        basename = origin.rsplit("/", 1)[-1]
        if basename.endswith(".git"):
            basename = basename[: -len(".git")]
        if basename == folder_name:
            return origin
    return None


def load_shell_data():
    config = load_config()
    with open(config["shell_cache_location"], "r") as file:
        shell_data = json.load(file)
    return shell_data

def set_origin(repo_dir, origin_url):
    run_git(repo_dir, "git", "remote", "set-url", "origin", origin_url)


def set_gitea_remote(repo_dir, folder_name):
    shell_data = load_shell_data()
    gitea_origins = shell_data.get("gitea_origins", [])
    gitea_origin = find_gitea_origin(gitea_origins, folder_name)
    if gitea_origin is None:
        print("No matching gitea origin found for folder '{}'".format(folder_name))
        sys.exit(1)
    set_origin(repo_dir, gitea_origin)
    print("Switched to gitea origin:", gitea_origin)


def set_github_remote(repo_dir, folder_name):
    shell_data = load_shell_data()
    github_dirs = shell_data.get("github_dirs", [])
    if folder_name not in github_dirs:
        print("Folder '{}' is not in github_dirs; refusing to switch to github origin".format(folder_name))
        sys.exit(1)
    config = load_config()
    github_origin = "git@github.com:{}/{}.git".format(config["github_username"], folder_name)
    set_origin(repo_dir, github_origin)
    print("Switched to github origin:", github_origin)


def main():
    if len(sys.argv) < 2:
        print("Usage: python set_repo.py <repo_directory_path>")
        sys.exit(1)

    repo_dir = sys.argv[1]
    folder_name = get_folder_name(repo_dir)
    current_origin = get_current_origin(repo_dir)
    print("Current origin:", current_origin)

    is_github = "github" in current_origin.lower()
    if is_github:
        set_gitea_remote(repo_dir, folder_name)
    else:
        set_github_remote(repo_dir, folder_name)


if __name__ == "__main__":
    main()
