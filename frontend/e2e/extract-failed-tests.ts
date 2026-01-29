import * as fs from 'fs';
import * as path from 'path';

function findErrorContextFiles(testResultsDir: string): Record<string, string> {
  const errorContextMap: Record<string, string> = {};

  if (!fs.existsSync(testResultsDir)) {
    return errorContextMap;
  }

  const entries = fs.readdirSync(testResultsDir, { withFileTypes: true });

  for (const entry of entries) {
    if (entry.isDirectory()) {
      const errorContextPath = path.join(testResultsDir, entry.name, 'error-context.md');
      if (fs.existsSync(errorContextPath)) {
        // Use directory name as key - it usually contains the test file name
        errorContextMap[entry.name] = errorContextPath;
      }
    }
  }

  return errorContextMap;
}

export function extractFailedTests(baseDir: string = __dirname): void {
  const resultsPath = path.join(baseDir, 'test-results', 'results.json');
  const failedPath = path.join(baseDir, 'test-results', 'failed.json');
  const testResultsDir = path.join(baseDir, 'test-results');

  if (!fs.existsSync(resultsPath)) {
    console.log('No results.json found at:', resultsPath);
    return;
  }

  console.log('Extracting failed tests from:', resultsPath);

  // Find all error-context.md files
  const errorContextFiles = findErrorContextFiles(testResultsDir);
  if (Object.keys(errorContextFiles).length > 0) {
    console.log(`Found ${Object.keys(errorContextFiles).length} error-context.md file(s)`);
  }

  try {
    const results = JSON.parse(fs.readFileSync(resultsPath, 'utf-8'));
    const failedTests = results.suites?.flatMap((suite: any) =>
      suite.specs?.filter((spec: any) =>
        spec.tests?.some((test: any) =>
          test.results?.some((result: any) =>
            result.status === 'failed' || result.status === 'timedOut'
          )
        )
      ).map((spec: any) => {
        // Try to find matching error-context.md file
        let errorContextPath: string | undefined;
        const testFileName = suite.file.replace(/^tests\//, '').replace(/\.pw\.ts$/, '');

        for (const [dirName, contextPath] of Object.entries(errorContextFiles)) {
          if (dirName.includes(testFileName)) {
            errorContextPath = contextPath;
            break;
          }
        }

        return {
          file: suite.file,
          title: spec.title,
          errorContextPath: errorContextPath ? path.relative(testResultsDir, errorContextPath) : undefined,
          tests: spec.tests.flatMap((test: any) =>
            test.results
              ?.filter((result: any) => result.status === 'failed' || result.status === 'timedOut')
              .map((result: any) => ({
                status: result.status,
                error: result.error,
                duration: result.duration,
                retry: result.retry,
              })) || []
          )
        };
      })
    ).filter(Boolean) || [];

    if (failedTests.length > 0) {
      fs.writeFileSync(failedPath, JSON.stringify({ failedTests, timestamp: new Date().toISOString() }, null, 2));
      console.log(`Created failed.json with ${failedTests.length} failed test(s) at:`, failedPath);
    } else {
      console.log('No failed tests found - all tests passed!');
    }
  } catch (error) {
    console.log('Error creating failed.json:', error);
  }
}

// Allow running as a script
if (require.main === module) {
  extractFailedTests();
}
