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
  try {
    const token = core.getInput('token');
    const checkUnmergedPr = core.getBooleanInput('check-unmerged-pr');
    const context = github.context;
    const prNumber = context.payload.pull_request.number;

    console.log(`Pull Request number: ${prNumber} checkUnmergedPr=${checkUnmergedPr}`);

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
      fork_url: mainPR.head.repo.clone_url,
      branch: mainPR.head.ref,
      description: description
    };
    fs.writeFileSync('.depends-on.json', JSON.stringify(changeJson));
    console.log(`writing .depends-on.json: ${JSON.stringify(changeJson)}`);

    // the bundle is in the dist sub-directory
    execSync(`${__dirname}/../stage1.py ${checkUnmergedPr}`, { encoding: 'utf-8' });
  } catch (error) {
    console.log(error);
    core.setFailed(error.message);
  }
}

run();
