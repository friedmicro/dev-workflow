from ast import Expression
import json
import subprocess
from pathlib import Path
import requests
import yaml
import time

with open("./serpentdevflowconfig.yaml", 'r') as file:
    data_dict = yaml.safe_load(file)

gitea_token = data_dict["gitea_token"]
gitea_host = data_dict["gitea_host"]
github_username = data_dict["github_username"]
github_repo_limit = data_dict["github_repo_limit"]
repo_exclusions_local = data_dict["repo_exclusions_local"]
repo_exclusions_local_exceptions = data_dict["repo_exclusions_local_exceptions"]
exclusions_backup = data_dict["exclusions_backup"]
exclusions_backup_exceptions = data_dict["exclusions_backup_exceptions"]
shell_cache_location = data_dict["shell_cache_location"]
repo_local_location = data_dict["repo_local_location"]
repo_backup_location = data_dict["repo_backup_location"]

serpent_shell_data = {}
serpent_shell_data["github_dirs"] = []
serpent_shell_data["github_user"] = github_username
serpent_shell_data["gitea_origins"] = []

def should_exclude_based_on_exclusion_list(exclusions, exclusion_exceptions, repo_url):
    for exclusion in exclusions:
        full_exclusion = process_prefix(exclusion)
        if full_exclusion in repo_url:
            for exclusion_exception in exclusion_exceptions:
                full_exclusion_exception = process_prefix(exclusion_exception)
                if full_exclusion_exception in repo_url:
                    return False
            return True
    return False


def process_prefix(repo_url):
    return gitea_host + repo_url


def should_exclude_from_local(repo_url):
    return should_exclude_based_on_exclusion_list(repo_exclusions_local, repo_exclusions_local_exceptions, repo_url)


def should_exclude_from_backup(repo_url):
    return should_exclude_based_on_exclusion_list(exclusions_backup, exclusions_backup_exceptions, repo_url)


def form_gitea_http_git(repo_url):
    return repo_url + ".git"


# This is likely also compatible with forgejo
def fetch_gitea_repos():
    page = 0
    repositories = []
    r = requests.get("{}/api/v1/repos/search?limit=50&page={}&token={}".format(gitea_host, page, gitea_token))
    while len(r.json()["data"]):
        repositories.extend(r.json()["data"])
        page = page + 1
        r = requests.get("{}/api/v1/repos/search?limit=50&page={}&token={}".format(gitea_host, page, gitea_token))

    http_urls = set()
    for repository in repositories:
        http_urls.add(repository["html_url"])

    backup_urls = []
    local_urls = []
    for http_url in http_urls:
        if not should_exclude_from_backup(http_url):
            backup_urls.append(http_url)
        if not should_exclude_from_local(http_url):
            local_urls.append(http_url)
    return backup_urls, local_urls


# Get upstream github repos so we can diff them locally and more easily change shells
# Write the username for git so that the client is able to construct the origin paths
def map_github_upstreams():
    github_api = "https://api.github.com/users"
    github_query = "{}/{}/repos?per_page={}".format(github_api, github_username, github_repo_limit)
    r = requests.get(github_query)
    repos = r.json()
    for repo in repos:
        serpent_shell_data["github_dirs"].append(repo["name"])


def get_dir_name(http_url):
    return http_url.split("/")[-1]


def sync_repo(http_url, git_root):
    git_directory = get_dir_name(http_url)
    try:
        if Path(git_root + "/" + git_directory).is_dir():
            result = subprocess.run(
                ["git", "pull"],
                cwd=git_root + "/" + git_directory,
                capture_output=True,
                text=True,
                check=True
            )
        else:
            print()
            result = subprocess.run(
                ["git", "clone", form_gitea_http_git(http_url)],
                cwd=git_root,
                capture_output=True,
                text=True,
                check=True
            )
        print("Git operation:\n", result.stdout)
    except subprocess.CalledProcessError as e:
        # Given an actual outage this will crash this script, but this is unlikely and the target user is a developer who is running this
        # manually so this code simplicity is worth the risk
        print("Git operation, call stack on follows (retrying): ")
        print(http_url)
        print(e.stderr)
        sync_repo(http_url, git_root)


def main():
    backup_urls, local_urls = fetch_gitea_repos()
    print("Backup URLs")
    for http_url in backup_urls:
        sync_repo(http_url, repo_backup_location)
        print(http_url)

    print("Personal URLs")
    for http_url in local_urls:
        serpent_shell_data["gitea_origins"].append(form_gitea_http_git(http_url))
        sync_repo(http_url, repo_local_location)
        print(http_url)

    map_github_upstreams()

    with open(shell_cache_location, "w") as file:
        json.dump(serpent_shell_data, file, indent=4)


if __name__ == "__main__":
    main()
