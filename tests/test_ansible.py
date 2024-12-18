import pathlib

import pytest
import yaml

import depends_on.ansible as ansible


@pytest.mark.parametrize(
    "galaxy_content, expected_name, should_return_none",
    [
        (
            """
namespace: vexxhost
name: kubernetes
version: 2.0.1
readme: README.md
authors:
  - Mohammed Naser <mnaser@vexxhost.com>
description: Ansible collection for deploying Kubernetes clusters
license:
  - GPL-3.0-or-later
dependencies:
  ansible.posix: ">=1.3.0"
  community.crypto: ">=2.2.3"
  community.general: ">=4.5.0"
  kubernetes.core: ">=2.3.2"
  vexxhost.containers: ">=1.3.0"
tags:
  - application
  - cloud
  - infrastructure
  - linux
repository: https://github.com/vexxhost/ansible-collection-kubernetes
documentation: https://github.com/vexxhost/ansible-collection-kubernetes/tree/main/docs
homepage: https://github.com/vexxhost/ansible-collection-kubernetes
issues: https://github.com/vexxhost/ansible-collection-kubernetes/issues
build_ignore:
  - .github
  - molecule
  - .pre-commit-config.yaml
""",
            "vexxhost.kubernetes",
            False,
        ),
        (
            """
name: kubernetes
version: 2.0.1
readme: README.md
""",
            "vexxhost.kubernetes",
            True,
        ),
    ],
)
def test_get_collection_name(
    tmp_path: pathlib.Path,
    galaxy_content: str,
    expected_name: str,
    should_return_none: bool,
):
    galaxy_path = tmp_path / "galaxy.yml"
    galaxy_path.write_text(galaxy_content)
    result = ansible.get_collection_name(tmp_path)

    if should_return_none:
        assert result is None
    else:
        assert result is not None
        assert result == expected_name


@pytest.mark.parametrize(
    "collection_name, requirements_content, info, container_mode, return_code, expected_requirements",
    [
        # Invalid - collection_name is None
        (
            None,
            """
roles:
  - name: ansible_security.ids_config
    src: https://github.com/ansible-security/ids_config
""",
            {},
            False,
            0,
            "",
        ),
        # Invalid - "collections" not in requirements
        (
            "foo",
            """
---
roles:
  - name: ansible_security.ids_config
    src: https://github.com/ansible-security/ids_config
        """,
            {},
            False,
            0,
            "",
        ),
        # collection not found
        (
            "foo",
            """
---
collections:
  - source: ./awx_collection
    type: dir
  - flowerysong.hvault
  - community.docker
                """,
            {},
            False,
            0,
            "",
        ),
        # Valid - collection found - not container
        (
            "flowerysong.hvault",
            """
---
collections:
  - source: ./awx_collection
    type: dir
  - flowerysong.hvault
  - community.docker
                """,
            {"path": "foo"},
            False,
            1,
            {
                "collections": [
                    {"source": "./awx_collection", "type": "dir"},
                    {"name": "flowerysong.hvault", "source": "foo", "type": "dir"},
                    "community.docker",
                ]
            },
        ),
        # Valid - collection found - container mode
        (
            "flowerysong.hvault",
            """
---
collections:
  - source: ./awx_collection
    type: dir
  - flowerysong.hvault
  - community.docker
                """,
            {
                "path": "foo",
                "fork_url": "https://github.com/foo/bar.git",
                "branch": "baz",
            },
            True,
            1,
            {
                "collections": [
                    {"source": "./awx_collection", "type": "dir"},
                    {
                        "name": "https://github.com/foo/bar.git",
                        "type": "git",
                        "version": "baz",
                    },
                    "community.docker",
                ]
            },
        ),
        # Valid - collection found - container mode - test data["name"]
        (
            "flowerysong.hvault",
            """
---
collections:
  - source: ./awx_collection
    type: dir
  - name: flowerysong.hvault
  - community.docker
                """,
            {
                "path": "foo",
                "fork_url": "https://github.com/foo/bar.git",
                "branch": "baz",
            },
            True,
            1,
            {
                "collections": [
                    {"source": "./awx_collection", "type": "dir"},
                    {
                        "name": "https://github.com/foo/bar.git",
                        "type": "git",
                        "version": "baz",
                    },
                    "community.docker",
                ]
            },
        ),
    ],
)
def test_substitute_collection(
    collection_name: str,
    requirements_content: str,
    info: dict,
    container_mode: bool,
    return_code: bool,
    expected_requirements: str,
):
    requirements = yaml.safe_load(requirements_content)
    assert requirements is not None
    result = ansible.substitute_collection(
        collection_name=collection_name,
        info=info,
        requirements=requirements,
        container_mode=container_mode,
    )

    assert result == return_code
    if result != 0:
        assert requirements == expected_requirements
