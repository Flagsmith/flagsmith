import { FullConfig } from '@playwright/test';
import fetch from 'node-fetch';
import flagsmith from 'flagsmith/isomorphic';
import Project from '../common/project';

async function globalSetup(config: FullConfig) {
  console.log('Starting global setup for E2E tests...');

  const e2eTestApi = `${process.env.FLAGSMITH_API_URL || Project.api}e2etests/teardown/`;
  let token = process.env.E2E_TEST_TOKEN
    ? process.env.E2E_TEST_TOKEN
    : process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`];

  // For local/dev testing, use the default token from docker-compose if not set
  if (!token && (process.env.E2E_LOCAL === 'true' || process.env.E2E_DEV === 'true')) {
    token = 'some-token';
  }

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

  // Teardown previous test data
  if (token) {
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
      } else {
        const errorMsg = `e2e teardown failed with status ${res.status}`;
        console.error('\n', '\x1b[31m', errorMsg, '\x1b[0m', '\n');
        if (process.env.E2E_LOCAL !== 'true' && process.env.E2E_DEV !== 'true') {
          throw new Error(errorMsg); // Fail tests early in CI if teardown fails
        }
      }
    } catch (error) {
      const errorMsg = `e2e teardown error: ${error.message || String(error)}`;
      console.error('\n', '\x1b[31m', errorMsg, '\x1b[0m', '\n');
      if (process.env.E2E_LOCAL !== 'true' && process.env.E2E_DEV !== 'true') {
        throw error; // Fail tests early in CI if teardown errors
      }
    }
  } else {
    // Only warn for local/dev testing, don't fail
    if (process.env.E2E_LOCAL === 'true' || process.env.E2E_DEV === 'true') {
      console.log('\n', '\x1b[33m', 'e2e teardown skipped (no token) - OK for local testing', '\x1b[0m', '\n');
    } else {
      const errorMsg = 'e2e teardown failed - no available token (set E2E_TEST_TOKEN or E2E_TEST_TOKEN_<ENV>)';
      console.error('\n', '\x1b[31m', errorMsg, '\x1b[0m', '\n');
      throw new Error(errorMsg); // Fail tests in CI if token is missing
    }
  }

  console.log('Starting E2E tests');
}

export default globalSetup;
