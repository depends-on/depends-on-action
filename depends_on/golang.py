"golang specific code for stage 3."

import os
import re
import sys


def process_golang(main_dir, dirs, container_mode):
    "Add replace directives in go.mod for the local dependencies."
    go_mod = os.path.join(main_dir, "go.mod")
    if not os.path.exists(go_mod):
        return False
    # get the list of github.com/... dependencies that are in the local dependencies
    github_mods = []
    with open(go_mod, "r", encoding="UTF-8") as in_stream:
        for line in in_stream.readlines():
            match = re.match(r"^(require)?\s*(github.com/.*?)\s", line)
            if match and match.group(2) in dirs:
                github_mods.append(match.group(2))
    # add the replace directives to go.mod for the local dependencies
    nb_replace = 0
    for mod in github_mods:
        if mod in dirs:
            if container_mode:
                # remove https:// at the beginning of the url and .git at the end
                fork_url = (
                    dirs[mod]["fork_url"]
                    .replace("https://", "", 1)
                    .replace(".git", "", 1)
                )
                print(
                    f'Adding replace directive in go.mod for {mod} => {fork_url} {dirs[mod]["branch"]}',
                    file=sys.stderr,
                )
                os.system(
                    f"set -x; go mod edit -replace {mod}={fork_url}@{dirs[mod]['branch']}"
                )
            else:
                print(
                    f'Adding replace directive in go.mod for {mod} => {dirs[mod]["path"]}',
                    file=sys.stderr,
                )
                os.system(f"set -x; go mod edit -replace {mod}={dirs[mod]['path']}")
            nb_replace += 1
    # if there is any change to go.mod, `go mod tidy` needs to be called to have a correct go.sums
    if nb_replace > 0:
        os.system("set -x; go mod tidy")
    return nb_replace > 0


# golang.py ends here
