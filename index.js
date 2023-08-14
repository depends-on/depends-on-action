const core = require('@actions/core');
const github = require('@actions/github');
const { execSync } = require('child_process');
const url = require('url');

async function run() {
  try {
    const token = core.getInput('token');
    const context = github.context;
    const prNumber = context.payload.pull_request.number;

    const octokit = github.getOctokit(token);

    // Get details of the main PR
    const { data: mainPR } = await octokit.rest.pulls.get({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber
    });

    const description = mainPR.body;
    console.log(`Pull Request Description: ${description}`);

    if (!description) {
      return
    }

    // Match all "Depends-On" lines and process each one
    const dependsOnStrings = mainPR.body.match(/Depends-On:\s*(.*)/gi);

    console.log(`All: ${dependsOnStrings}`);

    if (!dependsOnStrings) {
      console.log('No Depends-On strings found.');
      return;
    }

    for (const dependsOnString of dependsOnStrings) {
      const dependsOnUrl = dependsOnString.match(/Depends-On:\s*(.*)/i)[1];
      const parsedUrl = url.parse(dependsOnUrl);
      const [owner, repo] = parsedUrl.pathname.split('/').slice(1, 3);
      const prNumber = parsedUrl.pathname.split('/').pop();

      // Construct the URL for cloning the repository
      const repoUrl = `https://github.com/${owner}/${repo}.git`;

      execSync(`cd .. && git clone ${repoUrl}`);

      // Get details of the dependent PR
      const { data: dependsOnPR } = await octokit.rest.pulls.get({
        owner,
        repo,
        pull_number: prNumber
      });

      if (dependsOnPR.merged) {
        console.log(`Dependent Pull Request ${prNumber} in ${owner}/${repo} is already merged.`);
      } else {
        execSync(`cd ../${repo} && git fetch origin pull/${prNumber}/head:pr-${prNumber} && git checkout pr-${prNumber}`);
      }

      console.log(`Dependent Pull Request ${prNumber} in ${owner}/${repo} cloned to ../${repo}`);
    }
  } catch (error) {
    core.setFailed(error.message);
  }
}

run();
