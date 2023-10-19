"javascript specific code for stage 3."

import json
import os
import sys


def load_package_json(package_json_path):
    """Load package.json file."""
    with open(package_json_path, "r", encoding="UTF-8") as package_json:
        return json.load(package_json)


def local_dependencies(dirs):
    """Return a dictionary of local dependencies with the name as key
    and the directory as value."""
    deps = {}
    for local_dir in dirs:
        local_path = dirs[local_dir]["path"]
        package_json_path = os.path.join(local_path, "package.json")
        if os.path.exists(package_json_path):
            deps[load_package_json(package_json_path)["name"]] = dirs[local_dir]
    return deps


def process_javascript(main_dir, dirs, container_mode):
    """Replace directive in package.json if present"""
    package_json_path = os.path.join(main_dir, "package.json")
    if not os.path.exists(package_json_path):
        return False
    package = load_package_json(package_json_path)
    if "dependencies" not in package:
        return False
    dependencies = package["dependencies"]
    local_deps = local_dependencies(dirs)
    count = 0
    for dependency in dependencies:
        if dependency in local_deps:
            if container_mode:
                info = local_deps[dependency]
                # remove https://github.com/ at the beginning and .git at the end
                repo = "git+" + info["fork_url"] + "#" + info["branch"]
                print(
                    f"Replacing {dependency} with remote version from {repo} in package.json",
                    file=sys.stderr,
                )
                dependencies[dependency] = repo
            else:
                print(
                    f"Replacing {dependency} with local version from {local_deps[dependency]['path']} in package.json",
                    file=sys.stderr,
                )
                dependencies[dependency] = "file:" + local_deps[dependency]["path"]
            count += 1
    with open(package_json_path, "w", encoding="UTF-8") as package_json:
        json.dump(package, package_json, indent=2)
    return count > 0


# javascript.py ends here
