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

  // Teardown previous test data
  const success = await runTeardown();
  if (!success) {
    throw new Error('E2E teardown failed');
  }

  console.log('Starting E2E tests');
}

export default globalSetup;
