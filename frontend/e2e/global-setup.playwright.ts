import { FullConfig } from '@playwright/test';
import fetch from 'node-fetch';
import flagsmith from 'flagsmith/isomorphic';
import Project from '../common/project';
import * as fs from 'fs';
import * as path from 'path';
import { runTeardown } from './teardown';

async function globalSetup(config: FullConfig) {
  console.log('Starting global setup for E2E tests...');

  const testResultsDir = path.join(__dirname, 'test-results');

  // Ensure test-results directory exists for the JSON reporter
  if (!fs.existsSync(testResultsDir)) {
    fs.mkdirSync(testResultsDir, { recursive: true });
  }

  const e2eTestApi = `${process.env.FLAGSMITH_API_URL || Project.api}e2etests/teardown/`;

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

  // Verify the server is running with E2E mode enabled
  const baseURL = `http://localhost:${process.env.PORT || 8080}`;
  try {
    const overridesRes = await fetch(`${baseURL}/config/project-overrides`);
    const overridesBody = await overridesRes.text();
    if (!overridesBody.includes('window.E2E=true')) {
      throw new Error(
        'Server is running WITHOUT E2E mode. Kill the existing server and re-run tests, ' +
        'or restart it with: cross-env E2E=true npm run start'
      );
    }
  } catch (e: any) {
    if (e.message?.includes('E2E mode')) throw e;
    throw new Error(`Cannot reach server at ${baseURL}: ${e.message}`);
  }

  // Teardown previous test data
  const success = await runTeardown();
  if (!success) {
    throw new Error('E2E teardown failed');
  }

  console.log('Starting E2E tests');
}

export default globalSetup;
