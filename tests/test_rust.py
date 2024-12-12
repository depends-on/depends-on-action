import pathlib
from unittest.mock import MagicMock, patch

import pytest

import depends_on.rust as rust


def return_log_dir(path: str = None) -> dict:
    """
    Returns a dictionary with the log crate directory structure.
    """
    return {
        "top_dir": "/home/foo/log",
        "path": "/home/foo/log" if path is None else path,
        "description": None,
        "fork_url": "https://github.com/leseb/log.git",
        "branch": "subdir",
        "main_url": "https://github.com/rust-lang/log.git",
        "main_branch": "main",
        "pr_number": "2",
        "merged": False,
        "subdir": None,
        "extra_dirs": [],
        "change_url": "https://github.com/rust-lang/log/pull/2",
    }


def return_env_logger_dir(path: str = None) -> dict:
    """
    Returns a dictionary with the env_logger crate directory structure.
    """
    return {
        "top_dir": "/home/foo/env_logger",
        "path": "/home/foo/env_logger",
        "description": None,
        "fork_url": "https://github.com/leseb/env_logger.git",
        "branch": "subdir",
        "main_url": "https://github.com/rust-cli/env_logger.git",
        "main_branch": "main",
        "pr_number": "2",
        "merged": False,
        "extra_dirs": [],
        "subdir": None,
        "change_url": "https://github.com/rust-cli/env_logger/pull/2",
    }


@pytest.mark.parametrize(
    "test_name, container_mode, dirs, expected_content, get_modules_return_value",
    [
        ##########
        # TEST 1 #
        ##########
        # container_mode = False
        # subdir = None
        (
            "test_no_container_mode_no_subdir",
            False,
            {
                "https://github.com/rust-lang/log": return_log_dir(),
            },
            """
[package]
name = "supertini"
version = "0.1.0"
edition = "2021"

[dependencies]
log = "0.4.0"

[patch.crates-io]
log = { path = "/home/foo/log" }
        """,
            {"log": return_log_dir()},
        ),
        ##########
        # TEST 2 #
        ##########
        # container_mode = True
        # subdir = None
        (
            "test_container_mode_no_subdir",
            True,
            {"https://github.com/rust-lang/log": return_log_dir()},
            """
[package]
name = "supertini"
version = "0.1.0"
edition = "2021"

[dependencies]
log = "0.4.0"

[patch.crates-io]
log = { git = "https://github.com/leseb/log.git", branch = "subdir" }
                """,
            {"log": return_log_dir()},
        ),
        ##########
        # TEST 3 #
        ##########
        # container_mode = False
        # subdir = subdir
        (
            "test_no_container_mode_subdir",
            False,
            {"https://github.com/rust-lang/log": return_log_dir()},
            """
[package]
name = "supertini"
version = "0.1.0"
edition = "2021"

[dependencies]
log = "0.4.0"

[patch.crates-io]
log = { path = "/home/foo/log/subdir" }
                """,
            {"log": return_log_dir("/home/foo/log/subdir")},
        ),
        ##########
        # TEST 4 #
        ##########
        # container_mode = False
        # subdir = None
        # multiple dirs passed
        (
            "test_no_container_nosubdir_multiple_dirs",
            False,
            {
                "https://github.com/rust-lang/log": return_log_dir(),
                "https://github.com/rust-cli/env_logger": return_env_logger_dir(),
            },
            """
[package]
name = "supertini"
version = "0.1.0"
edition = "2021"

[dependencies]
log = "0.4.0"

[patch.crates-io]
log = { path = "/home/foo/log" }
env_logger = { path = "/home/foo/env_logger" }
        """,
            {
                "log": return_log_dir(),
                "env_logger": return_env_logger_dir(),
            },
        ),
    ],
    ids=lambda val: val[-1] if isinstance(val, str) else None,
)
@patch("depends_on.rust.get_crates")
def test_process_rust(
    mock_get_modules,
    tmp_path: pathlib.Path,
    test_name,
    container_mode,
    dirs,
    expected_content,
    get_modules_return_value,
):
    mock_get_modules.return_value = get_modules_return_value

    # Arrange
    main_dir = tmp_path
    cargo_file = main_dir / "Cargo.toml"
    cargo_file.write_text(
        """
[package]
name = "supertini"
version = "0.1.0"
edition = "2021"

[dependencies]
log = "0.4.0"
"""
    )

    # Act & Assert
    result = rust.process_rust(main_dir, dirs, container_mode)
    assert result is not None
    assert cargo_file.read_text().strip() == expected_content.strip()


@patch("depends_on.rust.subprocess.run")
def test_lookup_name(mock_subprocess):
    carg_manifest_output = """
{"name":"supertini","version":"0.1.0"}
"""

    mock_result = MagicMock()
    mock_result.stdout = carg_manifest_output
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_subprocess.return_value = mock_result

    result = rust.get_rust_project_name("supertini")

    assert result is not None
    assert result == "supertini"
