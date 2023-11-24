"Functions used by multiple stages."

import json
import os
import re
import sys
from urllib.request import Request, urlopen


def get_pull_request_info(org, repo, pr_number):
    "Get the information about the Pull request."

    token = os.environ.get("GITHUB_TOKEN")

    # get the information about the Pull request using the GitHub API
    # set the Authorization header to use the token
    req = Request(
        f"https://api.github.com/repos/{org}/{repo}/pulls/{pr_number}",
    )
    req.add_header("Accept", "application/vnd.github.v3+json")
    if token:
        print("Using GitHub token", file=sys.stderr)
        req.add_header("Authorization", f"token {token}")
    with urlopen(req) as response:
        response_content = response.read()
    response_content.decode("utf-8")
    pr_info = json.loads(response_content)

    return pr_info


def get_gerrit_change_info(gerrit_url, gerrit_change_id):
    "Get the information about the Gerrit change."

    # get the information about the Gerrit change using the Gerrit API
    req = Request(
        f"{gerrit_url}/changes/{gerrit_change_id}?o=CURRENT_REVISION&o=CURRENT_COMMIT",
    )
    req.add_header("Accept", "application/json")
    with urlopen(req) as response:
        response_content = response.read()
    # remove the magic prefix
    response_content = re.sub(r"^\)\]\}\'\n", "", response_content.decode("utf-8"))
    change_info = json.loads(response_content)

    return change_info


def extract_pull_request(depends_on_url, check_mode):
    "Extract the dependency by git cloning the repository in the right branch for the Pull request."
    # parse the URL to extract the repo, org and pr number
    # the format is https://github.com/<org>/<repo>/pull/<pr_number>?subdir=<subdir>&<key>=<value>
    url_parts = depends_on_url.split("/")
    if len(url_parts) != 7:
        raise ValueError(f"Invalid URL {depends_on_url}")
    org = url_parts[3]
    repo = url_parts[4]
    pr_data = url_parts[6].split("?", 1)
    pr_number = pr_data[0]
    if len(pr_data) == 2:
        pr_data = pr_data[1].split("&")
        pr_data = {x.split("=")[0]: x.split("=")[1] for x in pr_data}
    else:
        pr_data = {}

    pr_info = get_pull_request_info(org, repo, pr_number)
    top_dir = os.path.realpath(repo)

    if not check_mode:
        # extract the dependency on disk
        extract_github_change(
            pr_info["head"]["repo"]["clone_url"],
            pr_info["head"]["ref"],
            pr_info["base"]["repo"]["clone_url"],
            pr_info["base"]["ref"],
            repo,
        )

        # save the information about the Pull request in depends-on.json
        data = {
            "description": pr_info["body"],
            "fork_url": pr_info["head"]["repo"]["clone_url"],
            "branch": pr_info["head"]["ref"],
            "main_url": pr_info["base"]["repo"]["clone_url"],
            "main_branch": pr_info["base"]["ref"],
            "topdir": top_dir,
            "path": top_dir,
            "merged": pr_info["merged"],
        }
        if "subdir" in pr_data:
            data["subdir"] = pr_data["subdir"]
            data["path"] = os.path.join(top_dir, pr_data["subdir"])
        with open(
            os.path.join(repo, "depends-on.json"), "w", encoding="UTF-8"
        ) as json_stream:
            json.dump(data, json_stream, indent=2)

        print(f"PR data: {data}", file=sys.stderr)
    return pr_info["merged"], top_dir


def extract_gerrit_review(depends_on_url, check_mode):
    "Extract the dependency by git cloning the repository in the right branch for the Gerrit change."
    # Parse the URL to extract the url and change number.
    # The format is
    # https://gerrit.wikimedia.org/r/c/mediawiki/extensions/ContentTranslation/+/123456
    # to extract https://gerrit.wikimedia.org/r and 123456
    url_parts = depends_on_url.split("/c/")
    if len(url_parts) != 2:
        raise ValueError(f"Invalid URL {depends_on_url}")
    gerrit_url = url_parts[0]
    change_parts = url_parts[1].split("/")
    change_id = change_parts[-1]
    # Get the information about the Gerrit change
    change_info = get_gerrit_change_info(gerrit_url, change_id)
    project = os.path.basename(change_info["project"])
    top_dir = os.path.realpath(project)
    if not check_mode:
        # extract the dependency on disk
        extract_gerrit_change(
            change_info["revisions"][change_info["current_revision"]]["fetch"][
                "anonymous http"
            ]["url"],
            change_info["revisions"][change_info["current_revision"]]["fetch"][
                "anonymous http"
            ]["ref"],
            change_info["branch"],
            project,
        )

        # save the information about the Gerrit change in depends-on.json
        data = {
            "description": change_info["revisions"][change_info["current_revision"]][
                "commit"
            ]["message"],
            "fork_url": change_info["revisions"][change_info["current_revision"]][
                "fetch"
            ]["anonymous http"]["url"],
            "branch": change_info["revisions"][change_info["current_revision"]][
                "fetch"
            ]["anonymous http"]["ref"],
            "main_url": change_info["revisions"][change_info["current_revision"]][
                "fetch"
            ]["anonymous http"]["url"],
            "main_branch": change_info["branch"],
            "topdir": top_dir,
            "path": top_dir,
            "merged": change_info["status"] == "MERGED",
        }
        with open(
            os.path.join(project, "depends-on.json"),
            "w",
            encoding="UTF-8",
        ) as json_stream:
            json.dump(data, json_stream, indent=2)

        print(f"Change data: {data}", file=sys.stderr)

    return change_info["status"] == "MERGED", top_dir


def extract_depends_on(depends_on_url, check_mode):
    "Extract the dependency by git cloning the repository in the right branch."
    if "/c/" in depends_on_url:
        return extract_gerrit_review(depends_on_url, check_mode)
    else:
        return extract_pull_request(depends_on_url, check_mode)


def extract_github_change(fork_url, branch, main_url, main_branch, repo):
    "Extract the dependency by git cloning the repository in the right branch for the Pull request."
    command(f"git clone --filter=tree:0 {main_url} {repo}")
    command(f"cd {repo} && git remote add pr {fork_url} && git fetch pr {branch}")
    # extract the master/main branch name
    command(f"cd {repo} && git checkout -b {branch} --track pr/{branch}")
    merge_main_branch(repo, main_branch)
    return repo


def extract_gerrit_change(change_url, branch, main_branch, repo):
    "Extract the dependency by git cloning the repository in the right branch for the Gerrit change."
    command(f"git clone --filter=tree:0 {change_url} {repo}")
    command(f"cd {repo} && git fetch {change_url} {branch} && git checkout FETCH_HEAD")
    merge_main_branch(repo, main_branch)
    return repo


def merge_main_branch(repo, main_branch):
    "Merge the main branch into the current branch."
    # set a dummy user name and email for the merge process to work
    command(
        f"cd {repo} && git config user.name 'Depends-On' && git config user.email 'depends-on@localhost' && git config commit.gpgsign false"
    )
    # merge the main branch into the current branch
    command(f"cd {repo} && git merge origin/{main_branch} --no-edit")
    return repo


def check_error(status, message):
    "Check the status and exit if it is false."
    if not status:
        raise Exception(message)


def command(cmd):
    "Execute a command"
    print(f"+ {cmd}", file=sys.stderr)
    ret = os.system(cmd)
    check_error(ret == 0, f"Command failed with exit code {ret}")


# common.py ends here
