import { execSync } from 'child_process';
import fetch from 'node-fetch';
import Project from '../common/project';

require('dotenv').config();

const RETRIES = parseInt(process.env.E2E_RETRIES || '1', 10);

async function runTeardown() {
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
  const delayMs = 2000; // 2 seconds between attempts

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
          console.log(''); // newline before retry message
        }
      }
    } catch (error) {
      console.error('\x1b[31m%s\x1b[0m', `✗ E2E teardown error: ${error}`);
      if (attempt < maxAttempts - 1) {
        console.log(''); // newline before retry message
      }
    }
  }

  console.log('\x1b[31m%s\x1b[0m\n', `✗ E2E teardown failed after ${maxAttempts} attempts`);
  return false;
}

function runPlaywright(args: string[], quietMode: boolean): boolean {
  try {
    // Quote arguments that contain spaces
    const quotedArgs = args.map(arg => arg.includes(' ') ? `"${arg}"` : arg);
    const playwrightCmd = ['npx', 'cross-env', 'NODE_ENV=production', 'E2E=true', 'playwright', 'test', ...quotedArgs];
    if (!quietMode) console.log('Running:', playwrightCmd.join(' '));
    execSync(playwrightCmd.join(' '), {
      stdio: 'inherit',
      env: process.env,
      shell: true,
    });
    return true;
  } catch (error) {
    return false;
  }
}

async function main() {
  let attempt = 0;

  // Get additional args passed to the script (e.g., test file names, -g patterns)
  const extraArgs = process.argv.slice(2);
  const verboseMode = process.env.VERBOSE === '1';
  const quietMode = !verboseMode;

  while (attempt <= RETRIES) {
    if (attempt > 0) {
      if (!quietMode) {
        console.log('\n==========================================');
        console.log(`Test attempt ${attempt} failed, running teardown and retrying failed tests only...`);
        console.log('==========================================\n');
      }
      await runTeardown();
    }

    const playwrightArgs = attempt > 0 ? ['--last-failed', ...extraArgs] : extraArgs;

    // Add --quiet flag if QUIET is set
    if (quietMode && !playwrightArgs.includes('--quiet')) {
      playwrightArgs.push('--quiet');
    }

    // First attempt: build bundle and run tests
    if (attempt === 0 && !process.env.SKIP_BUNDLE) {
      if (!quietMode) console.log('Building test bundle...');
      try {
        execSync('npm run test:bundle', { stdio: quietMode ? 'ignore' : 'inherit' });
      } catch (error) {
        console.error('Failed to build test bundle');
        process.exit(1);
      }
    } else if (attempt === 0 && process.env.SKIP_BUNDLE) {
      if (!quietMode) console.log('Skipping bundle build (SKIP_BUNDLE=1)');
    }

    if (!quietMode) console.log(attempt > 0 ? 'Running failed tests...' : 'Running all tests...');
    const success = runPlaywright(playwrightArgs, quietMode);

    if (success) {
      if (!quietMode) {
        console.log('\n==========================================');
        console.log(attempt > 0
          ? `Tests passed on attempt ${attempt} (after retrying failed tests)`
          : `Tests passed on attempt ${attempt}`);
        console.log('==========================================\n');
      }
      process.exit(0);
    }

    attempt++;
  }

  if (!quietMode) {
    console.log('\n==========================================');
    console.log(`Tests failed after ${RETRIES} retries`);
    console.log('==========================================\n');
  }
  process.exit(1);
}

main();
