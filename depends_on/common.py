"Functions used by multiple stages."

import os
import sys


def extract_github_change(fork_url, branch, main_url, main_branch, repo):
    "Extract the dependency by git cloning the repository in the right branch for the Pull request."
    command(f"git clone --filter=tree:0 {main_url} {repo}")
    command(f"cd {repo} && git remote add pr {fork_url} && git fetch pr {branch}")
    # extract the master/main branch name
    command(f"cd {repo} && git checkout -b {branch} --track pr/{branch}")
    # set a dummy user name and email for the merge process to work
    command(
        f"cd {repo} && git config user.name 'Depends-On' && git config user.email 'depends-on@localhost'"
    )
    # merge the main branch into the PR branch
    command(f"cd {repo} && git merge origin/{main_branch} --no-edit")
    return repo


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


# common.py ends here
