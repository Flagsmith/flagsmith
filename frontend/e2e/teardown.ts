import fetch from 'node-fetch';
import Project from '../common/project';

// Load environment variables
require('dotenv').config();

export async function runTeardown(): Promise<boolean> {
  console.log('\n\x1b[36m%s\x1b[0m\n', 'Running E2E teardown...');

  const e2eTestApi = `${process.env.FLAGSMITH_API_URL || Project.api}e2etests/teardown/`;
  const token = process.env.E2E_TEST_TOKEN
    ? process.env.E2E_TEST_TOKEN
    : process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`];

  if (!token) {
    console.error('\x1b[31m%s\x1b[0m\n', 'Error: No E2E_TEST_TOKEN found');
    return false;
  }

  const maxAttempts = 3;
  const delayMs = 2000;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    if (attempt > 0) {
      console.log(`\x1b[33m%s\x1b[0m`, `Retrying teardown (attempt ${attempt + 1}/${maxAttempts})...`);
      await new Promise(resolve => setTimeout(resolve, delayMs));
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
        return true;
      } else {
        console.error('\x1b[31m%s\x1b[0m', `✗ E2E teardown failed: ${res.status}`);
        if (attempt < maxAttempts - 1) {
          console.log('');
        }
      }
    } catch (error) {
      console.error('\x1b[31m%s\x1b[0m', `✗ E2E teardown error: ${error}`);
      if (attempt < maxAttempts - 1) {
        console.log('');
      }
    }
  }

  console.log('\x1b[31m%s\x1b[0m\n', `✗ E2E teardown failed after ${maxAttempts} attempts`);
  return false;
}

// When run directly as a script
if (require.main === module) {
  runTeardown().then(success => {
    process.exit(success ? 0 : 1);
  });
}
