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
      clone_url: mainPR.head.repo.clone_url,
      branch: mainPR.head.ref
    };
    fs.writeFileSync('.depends-on.json', JSON.stringify(changeJson));
    console.log(`writing .depends-on.json: ${JSON.stringify(changeJson)}`);

    // Match all "Depends-On" lines and process each one
    const dependsOnStrings = mainPR.body.match(/Depends-On:\s*(.*)/gi);

    console.log(`All: ${dependsOnStrings}`);

    // Match Main-Dir: for debugging purpose
    const mainDirRes = mainPR.body.match(/Main-Dir:\s*(.*)/i);

    const mainDir = mainDirRes ? mainDirRes[1] : '.';

    if (!dependsOnStrings) {
      console.log('No Depends-On strings found.');
      return;
    }

    let nbUnMergedPr = 0;

    for (const dependsOnString of dependsOnStrings) {
      const dependsOnUrl = dependsOnString.match(/Depends-On:\s*(.*)/i)[1];
      const parsedUrl = new URL(dependsOnUrl);
      const params = new URLSearchParams(parsedUrl.search);
      const [owner, repo] = parsedUrl.pathname.split('/').slice(1, 3);
      const prNumber = parsedUrl.pathname.split('/').pop();
      const subdir = params.get('subdir');

      // Construct the URL for cloning the repository
      const repoUrl = `https://github.com/${owner}/${repo}.git`;

      if (!checkUnmergedPr){
        myExecSync(`cd .. && git clone ${repoUrl}`);
      }

      // Get details of the dependent PR
      const { data: dependsOnPR } = await octokit.rest.pulls.get({
        owner,
        repo,
        pull_number: prNumber
      });

      if (dependsOnPR.merged) {
        console.log(`Dependent Pull Request ${prNumber} in ${owner}/${repo} is already merged.`);
      } else {
        nbUnMergedPr++;
        if (!checkUnmergedPr){
          myExecSync(`cd ../${repo} && git fetch origin pull/${prNumber}/head:pr-${prNumber} && git checkout pr-${prNumber}`);
          var dependsOnJson = {
            clone_url: dependsOnPR.head.repo.clone_url,
            branch: dependsOnPR.head.ref
          };
          if (subdir) {
            dependsOnJson.subdir = subdir;
          };
          fs.writeFileSync(`../${repo}/.depends-on.json`, JSON.stringify(dependsOnJson));
          console.log(`writing ../${repo}/.depends-on.json: ${JSON.stringify(dependsOnJson)}`);
        }
      }
      if (!checkUnmergedPr) {
        console.log(`Dependent Pull Request ${prNumber} in ${owner}/${repo} cloned to ../${repo}`);
      }
    }

    console.log(`checkUnmergedPr=${checkUnmergedPr} nbUnMergedPr${nbUnMergedPr}`);
    if (checkUnmergedPr && nbUnMergedPr > 0) {
      core.setFailed(`There are ${nbUnMergedPr} unmerged PRs!`);
      return;
    }
    console.log(`There are ${nbUnMergedPr} unmerged PRs`);
    myExecSync(`cd ${mainDir} && ${__dirname}/../depends-on`);
  } catch (error) {
    console.log(error);
    core.setFailed(error.message);
  }
}

run();
