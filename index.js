// -*- javascript -*-
const core = require('@actions/core');
const github = require('@actions/github');
const { execSync } = require('child_process');
const url = require('url');
const fs = require('fs');

function myExecSync(cmd) {
  console.log(`+ ${cmd}`);
  const output = execSync(cmd, { encoding: 'utf-8' });
  console.log(`${output}`);
  return output;
}

async function run() {
  const token = core.getInput('token');
  const checkUnmergedPr = core.getBooleanInput('check-unmerged-pr');
  const extraDirs = core.getInput('extra-dirs');
  const path = core.getInput('path');
  const context = github.context;

  try {
    if (!context.payload.pull_request) {
      console.log('Not a pull request. Skipping');
      return;
    }

    const prNumber = context.payload.pull_request.number;

    console.log(`Pull Request number: ${prNumber} checkUnmergedPr=${checkUnmergedPr}`);

    // change director if path is set
    if (path) {
      process.chdir(path);
    }

    myExecSync('pwd');

    const octokit = github.getOctokit(token);

    // Get details of the main PR
    const { data: mainPR } = await octokit.rest.pulls.get({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber
    });

    const description = mainPR.body;
    console.log(`description: ${description}`);

    if (!description) {
      return
    }

    const changeJson = {
      description: description,
      fork_url: mainPR.head.repo.clone_url,
      branch: mainPR.head.ref,
      pr_number: prNumber,
      main_url: mainPR.base.repo.clone_url,
      main_branch: mainPR.base.ref,
      change_url: mainPR.html_url,
      extra_dirs: extraDirs ? extraDirs.split(' ') : [],
    };
    fs.writeFileSync('depends-on.json', JSON.stringify(changeJson));
    console.log(`writing depends-on.json: ${JSON.stringify(changeJson)}`);

    // export token as the GITHUB_TOKEN env variable
    core.exportVariable('GITHUB_TOKEN', token);
  } catch (error) {
    core.setFailed(error.message);
    process.exit(1);
  }

  try {
    // the bundle is in the dist sub-directory
    execSync(`${__dirname}/../depends_on_stage2 ${checkUnmergedPr}`, { encoding: 'utf-8' });
  } catch (error) {
    if (checkUnmergedPr) {
      core.setFailed("Unmerged PRs found");
    } else {
      core.setFailed("stage 2 or 3 failed");
    }
    process.exit(1);
  }
}

run();
