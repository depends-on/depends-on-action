"javascript specific code for stage 3."

import glob
import json
import os

from depends_on.common import log


def load_package_json(package_json_path):
    """Load package.json file."""
    with open(package_json_path, "r", encoding="UTF-8") as package_json:
        return json.load(package_json)


def local_dependencies(dirs):
    """Return a dictionary of local dependencies with the name as key
    and the directory as value. It also looks for workspaces in package.json."""
    deps = {}
    for local_dir in dirs:
        if "subdir" in dirs[local_dir]:
            local_path = os.path.join(
                dirs[local_dir]["path"], dirs[local_dir]["subdir"]
            )
        else:
            local_path = dirs[local_dir]["path"]
        package_json_path = os.path.join(local_path, "package.json")
        if os.path.exists(package_json_path):
            package = load_package_json(package_json_path)
            deps[package["name"]] = dirs[local_dir]
            if "workspaces" in package and "packages" in package["workspaces"]:
                log("detected workspaces")
                for workspace_glob in package["workspaces"]["packages"]:
                    log(f"processing {workspace_glob}")
                    for workspace_dir in glob.glob(
                        os.path.join(local_path, workspace_glob)
                    ):
                        log(f"found subdir={workspace_dir}")
                        workspace_path = os.path.join(local_path, workspace_dir)
                        log(f"checking workspace {workspace_path} for package.json")
                        workspace_package_json_path = os.path.join(
                            workspace_path, "package.json"
                        )
                        if os.path.exists(workspace_package_json_path):
                            workspace_package = load_package_json(
                                workspace_package_json_path
                            )
                            log(f"found package {workspace_package['name']}")
                            deps[workspace_package["name"]] = {
                                "path": workspace_path,
                                "subdir": workspace_dir[len(local_path) + 1 :],
                                "fork_url": dirs[local_dir]["fork_url"],
                                "branch": dirs[local_dir]["branch"],
                            }
    return deps


def process_dependencies(dependencies, dirs, container_mode, package_json_path):
    """Process dependencies in package.json and replace local dependencies"""
    local_deps = local_dependencies(dirs)
    log(f"Found {len(local_deps)} local dependencies: {local_deps=}")
    count = 0
    for dependency in dependencies:
        if dependency in local_deps:
            if container_mode:
                info = local_deps[dependency]
                repo = "git+" + info["fork_url"] + "#" + info["branch"]
                log(
                    f"Replacing {dependency} with remote version from {repo} in package.json"
                )
                dependencies[dependency] = repo
            else:
                log(
                    f"Replacing {dependency} with local version from {local_deps[dependency]['path']} in package.json"
                )
                dependencies[dependency] = "file:" + local_deps[dependency]["path"]
            count += 1
    return count


def process_javascript(main_dir, dirs, container_mode):
    """Use changes from PR in package.json if present"""
    package_json_path = os.path.join(main_dir, "package.json")
    if not os.path.exists(package_json_path):
        return False
    log("Detected package.json file, checking for local dependencies")
    package = load_package_json(package_json_path)
    if "dependencies" not in package:
        return False
    dependencies = package["dependencies"]
    count = process_dependencies(dependencies, dirs, container_mode, package_json_path)
    if "devDependencies" in package:
        dependencies = package["devDependencies"]
        count += process_dependencies(
            dependencies, dirs, container_mode, package_json_path
        )
    with open(package_json_path, "w", encoding="UTF-8") as package_json:
        json.dump(package, package_json, indent=2)
    return count > 0


# javascript.py ends here
