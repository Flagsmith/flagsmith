import { test as setup } from '@playwright/test';
import Project from '../../common/project';



require('dotenv').config()


async function runAPITeardown() {
  const e2eTestApi = `${process.env.FLAGSMITH_API_URL || Project.api}e2etests/teardown/`
  const token = process.env.E2E_TEST_TOKEN
    ? process.env.E2E_TEST_TOKEN
    : process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`];

  console.log(`E2E using API: ${e2eTestApi}`)

  if (token) {
    try {
      const response = await fetch(e2eTestApi, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-E2E-Test-Auth-Token': token.trim(),
        },
        body: JSON.stringify({}),
      });

      if (response.ok) {
        console.log('\n\x1b[32m%s\x1b[0m\n', 'e2e teardown successful');
      } else {
        console.error('\n\x1b[31m%s\x1b[0m\n', `e2e teardown failed ${response.status}`);
      }
    } catch (error) {
      console.error('\n\x1b[31m%s\x1b[0m\n', 'e2e teardown failed - request error');
    }
  } else {
    console.error('\n\x1b[31m%s\x1b[0m\n', 'e2e teardown failed - no available token');
  }
}

setup('API teardown', async ({ }) => {
  await runAPITeardown();
});
