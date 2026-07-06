"Python specific code for stage 3."

import json
import os
import subprocess

from depends_on.common import log

CARGO_FILE = "Cargo.toml"


def get_rust_project_name(crate_path) -> str:
    """
    Lookup the name of a Rust project.
    "Use cargo's manifest reader to extract project details, avoiding manual parsing.
    """
    try:
        # Execute the `cargo read-manifest` command with the specified arguments We don't use the
        # built-in toml library because it doesn't support the syntax used in Cargo.toml Especially
        # the form 'log = { version = "0.4.0" }'
        result = subprocess.run(
            [
                "cargo",
                "read-manifest",
                "--quiet",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            cwd=crate_path,  # execute the command within the module directory
        )

        project_name = result.stdout.strip()
        json_output = result.stdout
        manifest = json.loads(json_output.strip())
        project_name = manifest.get("name", "").strip()

        return project_name

    except subprocess.CalledProcessError as e:
        raise ValueError(f"Error executing 'cargo read-manifest': {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON: {e}") from e


def get_crates(dirs) -> dict:
    """
    Get the dictionary of Rust crates from the local dependencies.
    """
    rust_mods = {}
    for _dir in dirs:
        if "subdir" in dirs[_dir] and dirs[_dir]["subdir"] is not None:
            path = os.path.join(dirs[_dir]["path"], dirs[_dir]["subdir"])
            name = get_rust_project_name(path)
            # Overwrite the path with the subdir so that subsequent calls to lookup_name will use
            # the nested correct path
            dirs[_dir]["path"] = path

        else:
            name = get_rust_project_name(dirs[_dir]["path"])
        if name:
            rust_mods[name] = dirs[_dir]
    return rust_mods


# Cargo has a command to add dependencies, but it needs to be installed
#   "cargo", "install", "cargo-edit"
# Then you can add a dependency with:
#   "cargo", "add", "log", "--path", "/home/foo/log"
def process_rust(main_dir, dep_dirs, container_mode) -> bool:
    """
    Add patch directives in Cargo.toml for the local dependencies.

    This function processes the Cargo.toml file in the specified main directory (the Rust project
    directory), identifies the dependencies (from dep_dirs), and adds replace directives for local
    dependencies based on the provided dependency directories and container mode.

    Args:
        main_dir (str): The main directory containing the Cargo.toml file. dep_dirs (dict): A
        dictionary of local dependencies with their paths or URLs. container_mode (bool): A flag
        indicating whether to use container mode for dependencies.

    Returns:
        bool: True if any replace directives were added, False otherwise.

    Raises:
        subprocess.CalledProcessError: If the `cargo read-manifest` command fails.
    """

    cargo_path = os.path.join(main_dir, CARGO_FILE)
    if not os.path.exists(cargo_path):
        log(f"{cargo_path} not found, not a Rust project!")
        return False
    log(f"processing {cargo_path}")

    # Find the list of modules in the dependencies
    # get_modules will find the modules in the dependencies to inject, so it returns the name and
    # the path of the module
    crates_dirs = get_crates(dep_dirs)
    log(f"{crates_dirs=}")
    nb_replace = 0

    for mod in crates_dirs.items():
        crate = mod[0]
        crate_path = mod[1]["path"]
        if container_mode:
            crate_fork_url = mod[1]["fork_url"]
            create_branch = mod[1]["branch"]
            # https://doc.rust-lang.org/cargo/reference/overriding-dependencies.html#the-patch-section
            crate_line = (
                f'{crate} = {{ git = "{crate_fork_url}", branch = "{create_branch}" }}'
            )
            insert_after_patch_crates_io(cargo_path, crate_line)
        else:
            log(f"Patching '{crate}' crate in '{cargo_path}' with '{crate_path}'")
            crate_line = f'{crate} = {{ path = "{crate_path}" }}'
            insert_after_patch_crates_io(cargo_path, crate_line)

        nb_replace += 1

    return nb_replace > 0


def insert_after_patch_crates_io(cargo_path, new_content) -> None:
    """
    Inserts new content after the "[patch.crates-io]" section in a Cargo.toml file.

    If the "[patch.crates-io]" section is not found, it appends the section and the new content at
    the end of the file.

    Args:
        cargo_path (str): The path to the Cargo.toml file.
        new_content (str): The new content to be inserted after the "[patch.crates-io]" section.
    """
    with open(cargo_path, "r", encoding="UTF-8") as file:
        lines = file.readlines()

    patch_crates_io_found = False
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if "[patch.crates-io]" in line:
            patch_crates_io_found = True
            continue
        if patch_crates_io_found and line.strip() == "":
            new_lines.append(new_content + "\n")
            patch_crates_io_found = False

        # If this is the last line, add the new content
        if patch_crates_io_found and line == lines[-1] and patch_crates_io_found:
            new_lines.append(new_content + "\n")

    # If [patch.crates-io] was not found, add it at the end
    if not patch_crates_io_found:
        new_lines.append("\n[patch.crates-io]\n")
        new_lines.append(new_content + "\n")

    with open(cargo_path, "w", encoding="UTF-8") as file:
        file.writelines(new_lines)


# rust.py ends here
