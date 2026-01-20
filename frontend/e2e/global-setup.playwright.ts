import { FullConfig } from '@playwright/test';
import fetch from 'node-fetch';
import flagsmith from 'flagsmith/isomorphic';
import Project from '../common/project';

async function globalSetup(config: FullConfig) {
  console.log('Starting global setup for E2E tests...');

  const e2eTestApi = `${process.env.FLAGSMITH_API_URL || Project.api}e2etests/teardown/`;
  const apiHealthUrl = `${process.env.FLAGSMITH_API_URL || Project.api}health`;
  const token = process.env.E2E_TEST_TOKEN
    ? process.env.E2E_TEST_TOKEN
    : process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`];

  console.log(
    '\n',
    '\x1b[32m',
    `E2E using API: ${e2eTestApi}. E2E URL: http://localhost:${process.env.PORT || 8080}`,
    '\x1b[0m',
    '\n',
  );

  // Wait for API to be ready (max 60 seconds)
  console.log('Waiting for API to be ready...');
  const maxWaitTime = 60000; // 60 seconds
  const startTime = Date.now();
  let apiReady = false;

  while (!apiReady && Date.now() - startTime < maxWaitTime) {
    try {
      const healthRes = await fetch(apiHealthUrl);
      if (healthRes.ok) {
        apiReady = true;
        console.log('\n', '\x1b[32m', 'API is ready', '\x1b[0m', '\n');
      } else {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds before retry
      }
    } catch (error) {
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds before retry
    }
  }

  if (!apiReady) {
    console.error('\n', '\x1b[31m', 'API health check failed - continuing anyway', '\x1b[0m', '\n');
  }

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
        console.error('\n', '\x1b[31m', 'e2e teardown failed', res.status, '\x1b[0m', '\n');
      }
    } catch (error) {
      console.error('\n', '\x1b[31m', 'e2e teardown error:', error, '\x1b[0m', '\n');
    }
  } else {
    console.error('\n', '\x1b[31m', 'e2e teardown failed - no available token', '\x1b[0m', '\n');
  }

  console.log('Starting E2E tests');
}

export default globalSetup;