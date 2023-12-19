"Ansible specific code for stage 3."

import os

import yaml

from depends_on.common import log


def get_collection_name(repo_dir):
    "Return the collection name from the galaxy.yml file."
    if os.path.exists(os.path.join(repo_dir, "galaxy.yml")):
        with open(
            os.path.join(repo_dir, "galaxy.yml"), "r", encoding="UTF-8"
        ) as in_stream:
            data = yaml.safe_load(in_stream)
            try:
                return data["namespace"] + "." + data["name"]
            except KeyError:
                pass
    return None


def substitute_collection(collection_name, info, requirements, container_mode):
    "Substitute the collection into the requirements."
    if collection_name is None or "collections" not in requirements:
        return 0
    for idx in range(len(requirements["collections"])):
        data = requirements["collections"][idx]
        if data == collection_name or (
            "name" in data and data["name"] == collection_name
        ):
            if container_mode:
                requirements["collections"][idx] = {
                    "name": info["fork_url"],
                    "version": info["branch"],
                    "type": "git",
                }
            else:
                requirements["collections"][idx] = {
                    "name": collection_name,
                    "source": info["path"],
                    "type": "dir",
                }
            log(f"Substituted {requirements['collections'][idx]} in requirements.yml")
            return 1
    return 0


def process_ansible(main_dir, dirs, container_mode):
    "Change the requirements.yml file to add the dependencies."
    requirements_yml = os.path.join(main_dir, "requirements.yml")
    if not os.path.exists(requirements_yml):
        return False
    log(f"Processing {requirements_yml}")
    with open(requirements_yml, "r", encoding="UTF-8") as in_stream:
        requirements = yaml.safe_load(in_stream)
    # add the dependencies from dirs
    nb_replace = 0
    for repo_name, info in dirs.items():
        collection_name = get_collection_name(info["path"])
        nb_replace += substitute_collection(
            collection_name, info, requirements, container_mode
        )
    # if there is a change to requirements.yml, write it back
    if nb_replace > 0:
        with open(requirements_yml, "w", encoding="UTF-8") as out_stream:
            yaml.dump(requirements, out_stream)
    return nb_replace > 0


# ansible.py ends here
