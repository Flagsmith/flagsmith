import { FullConfig } from '@playwright/test';
import fetch from 'node-fetch';
import flagsmith from 'flagsmith/isomorphic';
import Project from '../common/project';
import * as fs from 'fs';
import * as path from 'path';

async function globalSetup(config: FullConfig) {
  console.log('Starting global setup for E2E tests...');

  const testResultsDir = path.join(__dirname, 'test-results');

  // Ensure test-results directory exists for the JSON reporter
  if (!fs.existsSync(testResultsDir)) {
    fs.mkdirSync(testResultsDir, { recursive: true });
  }

  const e2eTestApi = `${process.env.FLAGSMITH_API_URL || Project.api}e2etests/teardown/`;
  const token = process.env.E2E_TEST_TOKEN
      ? process.env.E2E_TEST_TOKEN
      : process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`]

  console.log(
    '\n',
    '\x1b[32m',
    `E2E using API: ${e2eTestApi}. E2E URL: http://localhost:${process.env.PORT || 8080}`,
    '\x1b[0m',
    '\n',
  );

  // Initialize Flagsmith
  await flagsmith.init({
    api: Project.flagsmithClientAPI,
    environmentID: Project.flagsmith,
    fetch,
  });

  // Teardown previous test data with retry logic
  if (!token) {
    const errorMsg = 'e2e teardown failed - no available token (set E2E_TEST_TOKEN or E2E_TEST_TOKEN_<ENV>)';
    console.error('\n', '\x1b[31m', errorMsg, '\x1b[0m', '\n');
    throw new Error(errorMsg);
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
        console.log('\n', '\x1b[32m', 'e2e teardown successful', '\x1b[0m', '\n');
        console.log('Starting E2E tests');
        return;
      }

      console.error('\x1b[31m%s\x1b[0m', `✗ E2E teardown failed: ${res.status}`);
      if (attempt < maxAttempts - 1) {
        console.log('');
      }
    } catch (error) {
      console.error('\x1b[31m%s\x1b[0m', `✗ E2E teardown error: ${error.message || String(error)}`);
      if (attempt < maxAttempts - 1) {
        console.log('');
      }
    }
  }

  const errorMsg = `e2e teardown failed after ${maxAttempts} attempts`;
  console.error('\n', '\x1b[31m', errorMsg, '\x1b[0m', '\n');
  throw new Error(errorMsg);
}

export default globalSetup;
