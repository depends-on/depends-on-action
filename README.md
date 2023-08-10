# depends-on-action

GitHub action to install dependent Pull Requests and configure them to be used
by later steps.

## Overview

This action allows you to install Pull Request dependencies when the workflow
action is triggered.

The action is extracting all the Pull Requests that are declared in
the description of the Pull Request with `Depends-On: <PR url>`
syntax.

It then injects the needed changes in the code to use the other Pull Requests. [to be done]

## Enabling the action

### Sample Configuration

Defining Github Actions requires that you create a directory
`.github/workflows` inside your repository.  Inside this directory you
create files which are processed when various events occur.

The simplest example of using this action would be to create the file
`.github/workflows/pull_request.yml` with the following contents:

```yaml
---
name: Pull Request
on:
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  validate-tests:
    name: Run tests
    runs-on: ubuntu-latest
    steps:

    - name: Checkout code
      uses: actions/checkout@master

    - name: Extract dependent Pull Requests
      uses: depends-on/depends-on-action@main
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
...
```

## Roadmap

- stage 1: javascript program to extract the dependencies.
- stage 2: python program to inject the dependencies into the main PR. Will be called from stage 1 or standalone.
- stage 3: check before merge. Could be a new action.

- [x] [stage 1: extract public PR](https://github.com/depends-on/depends-on-action/issues/2)
- [ ] [stage 2: go support](https://github.com/depends-on/depends-on-action/issues/3)
- [ ] [stage 2: custom injection](https://github.com/depends-on/depends-on-action/issues/4)
- [ ] [stage 2: Github action support](https://github.com/depends-on/depends-on-action/issues/5)
- [ ] [stage 1: gerrit support for software-factory.io](https://github.com/depends-on/depends-on-action/issues/6)
- [ ] [stage 1: extract private PR](https://github.com/depends-on/depends-on-action/issues/7)
- [ ] [stage 2: python support](https://github.com/depends-on/depends-on-action/issues/8)
- [ ] [stage 2: ansible support](https://github.com/depends-on/depends-on-action/issues/9)
- [ ] [stage 3: prevent merging if a dependent PR isn't merged](https://github.com/depends-on/depends-on-action/issues/10)
- [ ] [stage 2: rust support](https://github.com/depends-on/depends-on-action/issues/11)
- [ ] [stage 2: javascript support](https://github.com/depends-on/depends-on-action/issues/12)
