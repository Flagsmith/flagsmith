import { execSync } from 'child_process';
import { runTeardown } from './teardown';
import * as fs from 'fs';
import * as path from 'path';

require('dotenv').config();

const RETRIES = parseInt(process.env.E2E_RETRIES || '1', 10);
const REPEAT = parseInt(process.env.E2E_REPEAT || '0', 10);
const RESULTS_DIR = path.join(__dirname, 'test-results');
const RESULTS_FILE = path.join(RESULTS_DIR, 'results.json');

function runPlaywright(args: string[], quietMode: boolean, isRetry: boolean, attemptNumber: number): boolean {
  try {
    // Quote arguments that contain spaces or special shell characters
    const quotedArgs = args.map(arg => {
      if (arg.includes(' ') || arg.includes('|') || arg.includes('&') || arg.includes(';')) {
        return `"${arg}"`;
      }
      return arg;
    });
    const playwrightCmd = ['npx', 'cross-env', 'NODE_ENV=production'];

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

function mergeResults(attemptFiles: string[]): void {
  if (attemptFiles.length === 0) return;

  // Read all results files
  const allResults = attemptFiles.map(file => {
    try {
      return JSON.parse(fs.readFileSync(file, 'utf8'));
    } catch (error) {
      console.error(`Warning: Failed to read ${file}`);
      return null;
    }
  }).filter(r => r !== null);

  if (allResults.length === 0) return;

  // Use the first result as the base
  const merged = allResults[0];

  // Merge suites and tests from subsequent attempts
  for (let i = 1; i < allResults.length; i++) {
    const result = allResults[i];

    // Merge test suites
    if (result.suites) {
      merged.suites = merged.suites || [];
      result.suites.forEach((suite: any) => {
        // Check if suite already exists
        const existingIndex = merged.suites.findIndex((s: any) => s.file === suite.file && s.title === suite.title);
        if (existingIndex >= 0) {
          // Merge specs from this suite
          const existingSuite = merged.suites[existingIndex];
          suite.specs?.forEach((spec: any) => {
            const specIndex = existingSuite.specs?.findIndex((s: any) => s.title === spec.title);
            if (specIndex >= 0) {
              // Replace the spec (retry succeeded, use new result)
              existingSuite.specs[specIndex] = spec;
            } else {
              // Add new spec
              existingSuite.specs = existingSuite.specs || [];
              existingSuite.specs.push(spec);
            }
          });
        } else {
          // Add new suite
          merged.suites.push(suite);
        }
      });
    }
  }

  // Recalculate stats
  let totalTests = 0;
  let passed = 0;
  let failed = 0;
  let flaky = 0;
  let skipped = 0;

  merged.suites?.forEach((suite: any) => {
    suite.specs?.forEach((spec: any) => {
      spec.tests?.forEach((test: any) => {
        totalTests++;
        if (test.status === 'expected') passed++;
        else if (test.status === 'unexpected') failed++;
        else if (test.status === 'flaky') flaky++;
        else if (test.status === 'skipped') skipped++;
      });
    });
  });

  // Update stats
  merged.stats = {
    ...merged.stats,
    expected: passed,
    unexpected: failed,
    flaky: flaky,
    skipped: skipped,
  };

  // Write merged results
  fs.writeFileSync(RESULTS_FILE, JSON.stringify(merged, null, 2));
}

async function main() {
  let attempt = 0;
  const attemptFiles: string[] = [];

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
        execSync('npm run bundle', { stdio: quietMode ? 'ignore' : 'inherit', env: { ...process.env, E2E: 'true' } });
      } catch (error) {
        console.error('Failed to build test bundle');
        process.exit(1);
      }
    } else if (attempt === 0 && process.env.SKIP_BUNDLE) {
      if (!quietMode) console.log('Skipping bundle build (SKIP_BUNDLE=1)');
    }

    if (!quietMode) console.log(attempt > 0 ? 'Running failed tests...' : 'Running all tests...');
    const success = runPlaywright(playwrightArgs, quietMode, attempt > 0, attempt);

    // Save results from this attempt if retries are enabled
    if (RETRIES > 0 && fs.existsSync(RESULTS_FILE)) {
      const attemptFile = path.join(RESULTS_DIR, `results-attempt-${attempt}.json`);
      fs.copyFileSync(RESULTS_FILE, attemptFile);
      attemptFiles.push(attemptFile);
    }

    if (success) {
      if (!quietMode) {
        console.log('\n==========================================');
        console.log(attempt > 0
            ? `Tests passed on attempt ${attempt} (after retrying failed tests)`
            : `Tests passed on attempt ${attempt}`);
        console.log('==========================================\n');
      }

      // If REPEAT is set and this is the first successful run, repeat the tests
      if (REPEAT > 0 && attempt === 0) {
        if (!quietMode) {
          console.log('\n==========================================');
          console.log(`Tests passed! Running ${REPEAT} additional time(s) to check for flakiness...`);
          console.log('==========================================\n');
        }

        for (let repeatAttempt = 1; repeatAttempt <= REPEAT; repeatAttempt++) {
          if (!quietMode) {
            console.log(`\nRepeat attempt ${repeatAttempt} of ${REPEAT}...`);
          }

          // Run the same tests again with the original arguments
          const repeatSuccess = runPlaywright(extraArgs, quietMode, false, 0);

          if (!repeatSuccess) {
            if (!quietMode) {
              console.log('\n==========================================');
              console.log(`FLAKY TEST DETECTED: Tests failed on repeat attempt ${repeatAttempt} of ${REPEAT}`);
              console.log('==========================================\n');
            }
            process.exit(1);
          }

          if (!quietMode) {
            console.log(`Repeat attempt ${repeatAttempt} of ${REPEAT} passed`);
          }
        }

        if (!quietMode) {
          console.log('\n==========================================');
          console.log(`All tests passed ${REPEAT + 1} time(s) - no flakiness detected!`);
          console.log('==========================================\n');
        }
      }

      // Merge results from all attempts if we had retries
      if (RETRIES > 0 && attemptFiles.length > 1) {
        if (!quietMode) console.log('Merging test results from all attempts...');
        mergeResults(attemptFiles);
        // Clean up attempt files
        attemptFiles.forEach(file => {
          try {
            fs.unlinkSync(file);
          } catch (error) {
            // Ignore cleanup errors
          }
        });
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
