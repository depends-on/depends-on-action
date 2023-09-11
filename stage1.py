#!/usr/bin/env python3

"Stage1: extract dependencies of the main changeset and call stage2."

import json
import os
import re
import sys
from urllib.request import Request, urlopen


def load_depends_on(from_dir):
    "Load the data from the .depends-on.json file"

    fname = os.path.join(from_dir, ".depends-on.json")

    with open(fname, "r", encoding="UTF-8") as json_stream:
        return json.load(json_stream)


def check_error(status, message):
    "Check the status and exit if it is false."
    if not status:
        print(message, file=sys.stderr)
        sys.exit(1)


def command(cmd):
    "Execute a command"
    print(f"+ {cmd}", file=sys.stderr)
    ret = os.system(cmd)
    check_error(ret == 0, f"Command failed with exit code {ret}")


def extract_github_change(fork_url, branch, main_url, main_branch, repo):
    "Extract the dependency by git cloning the repository in the right branch for the Pull request."
    command(f"git clone --filter=tree:0 {main_url}")
    command(f"cd {repo} && git remote add pr {fork_url} && git fetch pr {branch}")
    # extract the master/main branch name
    command(f"cd {repo} && git checkout -b {branch} --track pr/{branch}")
    # set a dummy user name and email for the merge process to work
    command(
        f"cd {repo} && git config user.name 'Depends-On' && git config user.email 'depends-on@localhost'"
    )
    # merge the main branch into the PR branch
    command(f"cd {repo} && git merge origin/{main_branch} --no-edit")


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


def extract_depends_on(depends_on_url, check_mode):
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

    if not check_mode:
        # extract the dependency on disk
        extract_github_change(
            pr_info["head"]["repo"]["clone_url"],
            pr_info["head"]["ref"],
            pr_info["base"]["repo"]["clone_url"],
            pr_info["base"]["ref"],
            repo,
        )

        # save the information about the Pull request in .depends-on.json
        top_dir = os.path.realpath(repo)
        data = {
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
            os.path.join(repo, ".depends-on.json"), "w", encoding="UTF-8"
        ) as json_stream:
            json.dump(data, json_stream, indent=2)

        print(f"PR data: {data}", file=sys.stderr)
    return pr_info["merged"]


def main(check_mode):
    "Main function."

    # get the current directory
    main_dir = os.getcwd()

    data = load_depends_on(main_dir)

    if "description" not in data:
        print("No description found.", file=sys.stderr)
        return 0

    depends_on = re.findall(
        r"^Depends-On: (.*)", data["description"], re.IGNORECASE | re.MULTILINE
    )

    if len(depends_on) == 0:
        print("No Depends-On found.", file=sys.stderr)
        return 0

    print(f"depends_on: {depends_on}", file=sys.stderr)

    # go to the top dir (above main_dir)
    os.chdir(os.path.join(main_dir, ".."))

    nb_unmerged_pr = 0
    for depends_on_url in depends_on:
        merged = extract_depends_on(depends_on_url, check_mode)
        if not merged:
            nb_unmerged_pr += 1

    print(f"{nb_unmerged_pr} unmerged PR", file=sys.stderr)

    if check_mode:
        return 1 if nb_unmerged_pr > 0 else 0

    if nb_unmerged_pr == 0:
        print("No unmerged PR found.", file=sys.stderr)
        return 0

    # extract the Main-Dir: <dir> string if any from the description
    main_dir_res = re.findall(
        r"^Main-Dir: (.*)", data["description"], re.IGNORECASE | re.MULTILINE
    )

    if len(main_dir_res) > 0:
        main_dir = main_dir_res[-1].strip()

    print(f"+ chdir {main_dir}", file=sys.stderr)
    os.chdir(main_dir)

    stage2 = os.path.join(os.path.dirname(__file__), "stage2.py")
    print(f"+ {stage2}", file=sys.stderr)
    os.execl(stage2, "stage2.py")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] == "true"))

# stage1.py ends here