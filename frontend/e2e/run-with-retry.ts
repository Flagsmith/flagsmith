import { execSync } from 'child_process';
import { runTeardown } from './teardown';

require('dotenv').config();

const RETRIES = parseInt(process.env.E2E_RETRIES || '1', 10);

function runPlaywright(args: string[], quietMode: boolean, isRetry: boolean): boolean {
  try {
    // Quote arguments that contain spaces or special shell characters
    const quotedArgs = args.map(arg => {
      if (arg.includes(' ') || arg.includes('|') || arg.includes('&') || arg.includes(';')) {
        return `"${arg}"`;
      }
      return arg;
    });
    const playwrightCmd = ['npx', 'cross-env', 'NODE_ENV=production', 'E2E=true'];

    // Skip cleanup on retries to preserve failed.json and test artifacts
    if (isRetry) {
      playwrightCmd.push('E2E_SKIP_CLEANUP=1');
    }

    playwrightCmd.push('playwright', 'test', ...quotedArgs);

    // Add -x flag for fail-fast mode when E2E_RETRIES=0
    if (process.env.E2E_RETRIES === '0' && !quotedArgs.includes('-x')) {
      playwrightCmd.push('-x');
    }

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

    // On retry, use --last-failed only if there were actual test failures
    // If global setup failed before tests ran, run all tests instead
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
    const success = runPlaywright(playwrightArgs, quietMode, attempt > 0);

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
