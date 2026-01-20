import fetch from 'node-fetch';
import Project from '../common/project';

// Load environment variables
require('dotenv').config();

async function runTeardown() {
  console.log('\n\x1b[36m%s\x1b[0m\n', 'Running E2E teardown...');

  const e2eTestApi = `${process.env.FLAGSMITH_API_URL || Project.api}e2etests/teardown/`;
  const token = process.env.E2E_TEST_TOKEN
    ? process.env.E2E_TEST_TOKEN
    : process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`];

  if (!token) {
    console.error('\x1b[31m%s\x1b[0m\n', 'Error: No E2E_TEST_TOKEN found');
    process.exit(1);
  }

  try {
    const res = await fetch(e2eTestApi, {
      body: JSON.stringify({}),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-E2E-Test-Auth-Token': token.trim(),
      },
      method: 'POST',
    });

    if (res.ok) {
      console.log('\x1b[32m%s\x1b[0m\n', '✓ E2E teardown successful');
    } else {
      console.error('\x1b[31m%s\x1b[0m\n', `✗ E2E teardown failed: ${res.status}`);
      process.exit(1);
    }
  } catch (error) {
    console.error('\x1b[31m%s\x1b[0m\n', `✗ E2E teardown error: ${error}`);
    process.exit(1);
  }
}

runTeardown();
