"golang specific code for stage 3."

import os
import re

from depends_on.common import log


def get_modules(go_mod_path):
    """
    Parses the go.mod file content into a structured dictionary.

    Args:
        go_mod_path (str): The go.mod file to use.

    Returns:
        dict: A structured representation of the required modules.
    """
    mods = []

    # Regular expressions to match require directives, excluding lines with "// indirect"
    single_line_require_re = re.compile(
        r"^require\s+(\S+)\s+(\S+)(?!.*\/\/\s+indirect)$"
    )
    multiline_require_re = re.compile(r"^(\S+)\s+(\S+)(?!.*\/\/\s+indirect)$")

    with open(go_mod_path, "r", encoding="UTF-8") as f:
        in_multiline_require = False
        multiline_requires = []

        for line in f.readlines():
            line = line.strip()  # strip to remove tabs and spaces for multiline require

            # Skip empty lines or comments
            if not line or line.startswith("//"):
                continue

            # Handle require directive (single-line or start of multi-line block)
            if line.startswith("require ("):
                in_multiline_require = True
                multiline_requires = []
                continue
            if in_multiline_require:
                if line == ")":  # End of multiline block
                    in_multiline_require = False
                    mods.extend(
                        multiline_requires
                    )  # use extend instead of append to merge lists
                else:
                    match = multiline_require_re.match(line)
                    if match:
                        multiline_requires.append(match.group(1))
                continue

            # Single-line require directive
            match = single_line_require_re.match(line)
            if match:
                mods.append(match.group(1))
                continue

    return mods


def process_golang(main_dir, dirs, container_mode):
    "Add replace directives in go.mod for the local dependencies."
    go_mod = os.path.join(main_dir, "go.mod")
    if not os.path.exists(go_mod):
        return False
    log(f"processing {go_mod}")
    # get the list of github.com/... dependencies that are in the local dependencies
    go_modules = get_modules(go_mod)
    if len(go_modules) == 0:
        raise ValueError("No Go modules found in the project")

    # add the replace directives to go.mod for the local dependencies
    nb_replace = 0
    for mod in go_modules:
        if mod in dirs:
            if container_mode:
                # remove https:// at the beginning of the url and .git at the end
                fork_url = (
                    dirs[mod]["fork_url"]
                    .replace("https://", "", 1)
                    .replace(".git", "", 1)
                )
                log(
                    f"Adding replace directive in go.mod for {mod} => {fork_url} {dirs[mod]['branch']}"
                )
                os.system(
                    f"set -x; go mod edit -replace {mod}={fork_url}@{dirs[mod]['branch']}"
                )
            else:
                log(
                    f"Adding replace directive in go.mod for {mod} => {dirs[mod]['path']}"
                )
                os.system(f"set -x; go mod edit -replace {mod}={dirs[mod]['path']}")
            nb_replace += 1
    # if there is any change to go.mod, `go mod tidy` needs to be called to have a correct go.sums
    if nb_replace > 0:
        os.system("set -x; go mod tidy")
    return nb_replace > 0


# golang.py ends here
