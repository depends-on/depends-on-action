# depends-on-action

GitHub action to install dependent Pull Requests and configure them to be used
by later steps.

## Overview

This action allows you to install Pull Request dependencies when the workflow
action is triggered.

You need this action if your project is split into multiple repositories, and you can have Pull Requests that must be tested together. It happens often when you have libraries or micro-services in different repositories, and you need to test changes with the programs that use them. Even if you depend on third-party repositories that are not yours, you can use this action to test your Pull Requests with the third-party Pull Requests.

How does it work? This GitHub action extracts all the Pull Requests that are declared in the description of the main Pull Request with the `Depends-On: <PR url>` syntax. You can have multiple dependencies in the description of the main Pull Request by adding multiple `Depends-On:` lines. For example, if you depend on a Pull Request in the `org/library` repository, you can add the following line in the description of your Pull Request:

```txt
Change to use the new library function

Depends-On: https://github.com/org/library/pull/123
```

If you need to specify a sub-directory for a particular Pull Request, use the following syntax:

```txt
Depends-On: <PR url>?subdir=<subdir path>
```

This GitHub action then injects the needed modifications in the code to use the other changes.

### Gerrit and Gitlab changes

Gerrit and Gitlab dependencies are also supported. Examples:

```txt
Depends-On: https://gerrit-review.googlesource.com/c/gerrit/+/394841
Depends-On: https://gitlab.com/adblockinc/ext/adblockplus/spec/-/merge_requests/428
```

The detection of the type of change is done in this order:

1. If there is a `/c/` in the url, it is a Gerrit change.
2. If there is `gitlab` in the hostname, it is a Gitlab change.
3. It is a Github change.

#### Gitlab credentials

If you need credentials to access the Gitlab server, you can set the environment variables `GITLAB_TOKEN` and `GITLAB_USER` as secrets. Depending on the configuration of your server, you could only need `GITLAB_TOKEN`.

### Go lang

For a Go lang change, the action adds `replace` directives for the dependencies inside the `go.mod` file. This action needs to be placed after installing the Go lang toolchain.

### Python

The action replaces entries in `requirements.txt` for a Python change with a `-e <local change>` or the equivalent for `pyproject.toml`.

### Javascript

The action replaces entries in `package.json` for Javascript change with `file:<local change>`.

### Container

The action auto-detects if a container is present and injects the changes in a compatible way if this is the case.

## Enabling the action

### Sample Configuration

Defining Github Actions requires creating a directory `.github/workflows` inside your repository. Inside this directory, you create files processed when various events occur.

The simplest example of using this action would be to create the file `.github/workflows/pull_request.yml` with the following contents:

```yaml
---
name: Pull Request
on:
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  validate-tests:
    runs-on: ubuntu-latest
    steps:

      - name: Checkout code
        uses: actions/checkout@v4

      # install the toolchain for your language

      - name: Extract dependent Pull Requests
        uses: depends-on/depends-on-action@0.12.0
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
        # optional if needed for Gitlab
        env:
          GITLAB_TOKEN: ${{ secrets.GITLAB_TOKEN }}
          GITLAB_USER: ${{ secrets.GITLAB_USER }}

      # <your usual actions here>

  check-all-dependencies-are-merged:
    runs-on: ubuntu-latest
    steps:

      - name: Checkout code
        uses: actions/checkout@v4

      - name: Check all dependent Pull Requests are merged
        uses: depends-on/depends-on-action@0.12.0
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          check-unmerged-pr: true
        # optional if needed for Gitlab
        env:
          GITLAB_TOKEN: ${{ secrets.GITLAB_TOKEN }}
          GITLAB_USER: ${{ secrets.GITLAB_USER }}
...
```

As demonstrated above, you need at least two pipelines: one or more to do your regular builds and tests injecting the dependent changes and, a specific one to block until the dependent changes are merged.

## Details

- stage 1: [javascript program](index.js) to extract the dependency information from the main change.
- stage 2: [depends_on_stage2 python program](depends_on_stage2) to extract the dependent changess
- stage 3: [depends_on_stage3 python program](depends_on_stage3) to inject the dependencies into the main change according to the detected programming languages.

When the action is called with the `check-unmerged-pr: true` setting, stages 1 and 2 are used but not stage 3. Stage 2, in this case, is not extracting the dependent changes on disk but just checking the merge status of all the dependent changes.

## Usage outside of a GitHub action

If you want to use the same dependency management in other CI pipelines or in a local test, you can install the python package:

```shellsession
$ pip install depends-on
```

and use the `depends_on_stage1` script as an entry point taking the URL of the change you want to download in parameter:

```shellsession
$ cd <workspace>
$ export GITHUB_TOKEN=<your token>
$ # if you need access to a private Gitlab server
$ export GITLAB_USER=<your user>
$ export GITLAB_TOKEN=<your gitlab token>
$ # Extracting a Github change and its dependencies
$ depends_on_stage1 https://github.com/depends-on/pyprog/pulls/2
$ # Extracting a Gitlab change and its dependencies
$ depends_on_stage1 https://gitlab.com/adblockinc/ext/adblockplus/spec/-/merge_requests/428
$ # Extracting a Gerrit change and its dependencies
$ depends_on_stage1 https://softwarefactory-project.io/r/c/dci-pipeline/+/29700
```

## Roadmap

- [x] [stage 1: extract public PR](https://github.com/depends-on/depends-on-action/issues/2)
- [x] [stage 3: go support](https://github.com/depends-on/depends-on-action/issues/3)
- [x] [stage 2: prevent merging if a dependent PR isn't merged](https://github.com/depends-on/depends-on-action/issues/10)
- [x] [stage 3: python support](https://github.com/depends-on/depends-on-action/issues/8)
- [x] [stage 3: python poetry support](https://github.com/depends-on/depends-on-action/issues/18)
- [x] [stage 3: python subdir support](https://github.com/depends-on/depends-on-action/issues/19)
- [x] [stage 3: container support](https://github.com/depends-on/depends-on-action/issues/17)
- [x] [stage 3: javascript support](https://github.com/depends-on/depends-on-action/issues/12)
- [x] [python package on pypi](https://github.com/depends-on/depends-on-action/issues/31)
- [x] [Non GitHub action usage](https://github.com/depends-on/depends-on-action/issues/32)
- [x] [stage 2: gerrit support](https://github.com/depends-on/depends-on-action/issues/6)
- [x] [stage 2: gitlab support](https://github.com/depends-on/depends-on-action/issues/5)
- [ ] [stage 3: ansible support](https://github.com/depends-on/depends-on-action/issues/9)
- [ ] [stage 3: custom injection](https://github.com/depends-on/depends-on-action/issues/4)
- [ ] [stage 2: extract private PR](https://github.com/depends-on/depends-on-action/issues/7)
- [ ] [stage 3: rust support](https://github.com/depends-on/depends-on-action/issues/11)
