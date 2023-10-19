"Python specific code for stage 3."

import os
import re
import sys


def lookup_name(fname):
    "Lookup the name of a module"
    if os.path.exists(fname):
        print(f"Looking up name in {fname}", file=sys.stderr)
        with open(fname, "r", encoding="UTF-8") as in_stream:
            for line in in_stream.readlines():
                match = re.match(r"^\s*name\s*=\s*['\"](.*?)['\"]\s*,", line)
                if match:
                    return match.group(1)
    return None


def get_modules(dirs):
    "Get the dictionary of python modules from the local dependencies."
    python_mods = {}
    for _dir in dirs:
        name = lookup_name(os.path.join(dirs[_dir]["path"], "setup.py")) or lookup_name(
            os.path.join(dirs[_dir]["path"], "pyproject.toml")
        )
        if name:
            python_mods[name] = dirs[_dir]
    return python_mods


def process_python_requirements(main_dir, dirs, container_mode):
    "Replace modules in requirements.txt for the local dependencies."
    requirements_txt = os.path.join(main_dir, "requirements.txt")
    requirements_txt_new = requirements_txt + ".new"
    if not os.path.exists(requirements_txt):
        return False
    print("requirements.txt detected", file=sys.stderr)
    module_dirs = get_modules(dirs)
    print(f"{module_dirs=}", file=sys.stderr)
    # replace the modules in requirements.txt
    nb_replace = 0
    with open(requirements_txt, "r", encoding="UTF-8") as in_stream:
        with open(requirements_txt_new, "w", encoding="UTF-8") as out_stream:
            for line in in_stream.readlines():
                match = re.match(r"^\s*(\w+)", line)
                if match and match.group(1) in module_dirs:
                    mod = match.group(1)
                    if container_mode:
                        # doc at https://pip.pypa.io/en/stable/cli/pip_install/#git
                        pkg = f"{mod} @ git+{module_dirs[mod]['fork_url']}@{module_dirs[mod]['branch']}"
                        if "subdir" in module_dirs[mod]:
                            pkg += (
                                f"#egg=subdir&subdirectory={module_dirs[mod]['subdir']}"
                            )
                        print(
                            f"Replacing {mod} in requirements.txt with {pkg}",
                            file=sys.stderr,
                        )
                        out_stream.write(f"{pkg}\n")
                    else:
                        print(
                            f"Replacing {mod} in requirements.txt with {module_dirs[mod]['path']}",
                            file=sys.stderr,
                        )
                        out_stream.write(f"-e {module_dirs[mod]['path']}\n")
                    nb_replace += 1
                else:
                    out_stream.write(line)
    os.rename(requirements_txt_new, requirements_txt)
    return nb_replace > 0


def process_python_pyproject(main_dir, dirs, container_mode):
    "Replace modules in pyproject.toml for the local dependencies."
    pyproject_toml = os.path.join(main_dir, "pyproject.toml")
    pyproject_toml_new = pyproject_toml + ".new"
    if not os.path.exists(pyproject_toml):
        return False
    print("pyproject.toml detected", file=sys.stderr)
    # get the list of python packages from local dependencies
    module_dirs = get_modules(dirs)
    print(f"{module_dirs=}", file=sys.stderr)
    # replace the modules in pyproject.toml
    nb_replace = 0
    with open(pyproject_toml, "r", encoding="UTF-8") as in_stream:
        with open(pyproject_toml_new, "w", encoding="UTF-8") as out_stream:
            for line in in_stream.readlines():
                match = re.match(r"^\s*(\w+)\s*=", line)
                if match and match.group(1) in module_dirs:
                    mod = match.group(1)
                    if container_mode:
                        # doc at https://python-poetry.org/docs/dependency-specification/#git-dependencies
                        pkg = f"{mod} = {{ git = \"{module_dirs[mod]['fork_url']}\", branch = \"{module_dirs[mod]['branch']}\""
                        if "subdir" in module_dirs[mod]:
                            pkg += (
                                f", subdirectory = \"{module_dirs[mod]['subdir']}\" }}"
                            )
                        else:
                            pkg += " }"
                        print(
                            f"Replacing {mod} in pyproject.toml with {pkg}",
                            file=sys.stderr,
                        )
                        out_stream.write(f"{pkg}\n")
                    else:
                        print(
                            f"Replacing {mod} in pyproject.toml with {module_dirs[mod]['path']}",
                            file=sys.stderr,
                        )
                        out_stream.write(
                            f'{mod} = {{ path = "{module_dirs[mod]["path"]}" }}\n'
                        )
                    nb_replace += 1
                else:
                    out_stream.write(line)
    os.rename(pyproject_toml_new, pyproject_toml)
    return nb_replace > 0


def process_python(main_dir, dirs, container_mode):
    "Process python dependencies."
    # process pyprohect.toml first because they can both be present
    # and it supposed to be the main one
    return process_python_pyproject(
        main_dir, dirs, container_mode
    ) or process_python_requirements(main_dir, dirs, container_mode)


# python.py ends here
