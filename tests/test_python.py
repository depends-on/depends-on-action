import pathlib

import pytest

import depends_on.python as python


@pytest.mark.parametrize(
    "file_content, expected_result, should_raise",
    [
        # Valid
        (
            """
[project]
name = "tmp-um0on3fwy6"
version = "0.1.0"
""",
            "tmp-um0on3fwy6",
            False,
        ),
        # Valid
        (
            """
[project]
name = 'tmp-um0on3fwy6'
description = "Add your description here"
""",
            "tmp-um0on3fwy6",
            False,
        ),
        # Valid
        (
            """
[project]
name = 'tmp-um0on3fwy6"
description = "Add your description here"
""",
            "tmp-um0on3fwy6",
            False,
        ),
        # Valid
        (
            """
[project]
name = "tmp-um0on3fwy6'
description = "Add your description here"
""",
            "tmp-um0on3fwy6",
            False,
        ),
        # Valid
        (
            """
[project]
authors = [{ name = "foo", email = "foo@bar.ai" }]
name = "tmp-um0on3fwy6"
description = "Add your description here"
""",
            "tmp-um0on3fwy6",
            False,
        ),
        # Valid
        (
            """
[project]
authors = [{ name = "foo", email = "foo@bar.ai" }]
name="tmp-um0on3fwy6"
description = "Add your description here"
""",
            "tmp-um0on3fwy6",
            False,
        ),
        # Valid
        (
            """
[project]
authors = [{ name = "foo", email = "foo@bar.ai" }]
name= "tmp-um0on3fwy6"
description = "Add your description here"
""",
            "tmp-um0on3fwy6",
            False,
        ),
        # Valid
        (
            """
[project]
authors = [{ name = "foo", email = "foo@bar.ai" }]
name ="tmp-um0on3fwy6"
description = "Add your description here"
""",
            "tmp-um0on3fwy6",
            False,
        ),
        # Valid
        (
            """
[build-system]
requires = ["setuptools>=70.1.0", "setuptools_scm>=8", "wheel"]
[project]
authors = [{ name = "foo", email = "foo@bar.ai" }]
name ="tmp-um0on3fwy6"
description = "Add your description here"
""",
            "tmp-um0on3fwy6",
            False,
        ),
        # Invalid - no name
        (
            """
[project]
version = "0.1.0"
description = "Add your description here"
""",
            None,
            True,
        ),
    ],
)
def test_lookup_pyproject_name_parametrized(
    tmp_path: pathlib.Path, file_content, expected_result, should_raise
):
    # Arrange
    main_dir = tmp_path
    pyproject = main_dir / "pyproject.toml"
    pyproject.write_text(file_content)

    # Act / Assert
    if should_raise:
        with pytest.raises(KeyError):
            python.lookup_pyproject_name(pyproject)
    else:
        result = python.lookup_pyproject_name(pyproject)
        assert result == expected_result


def test_lookup_setuppy_name(tmp_path: pathlib.Path):
    # Arrange
    main_dir = tmp_path
    pyproject = main_dir / "pyproject.toml"
    pyproject.write_text(
        """
import json

from setuptools import setup

setup(
    name="depends-on",
    description="A Python library to manage dependencies between changes.",
    long_description_content_type="text/markdown",
    long_description=open("README.md").read(),
    author="The Depends-On Team",
)
"""
    )

    # Act
    result = python.lookup_setuppy_name(pyproject)

    # Assert
    assert result is not None
    assert result == "depends-on"
