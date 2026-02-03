import * as fs from 'fs';
import * as path from 'path';

type ErrorContextMap = Record<string, string>;

const isFailedResult = (result: any) =>
  result.status === 'failed' || result.status === 'timedOut';

const hasFailedTests = (spec: any) =>
  spec.tests?.some((test: any) => test.results?.some(isFailedResult));

const getFailedSpecs = (suite: any) =>
  suite.specs?.filter(hasFailedTests) || [];

function findErrorContextFiles(testResultsDir: string): ErrorContextMap {
  if (!fs.existsSync(testResultsDir)) {
    return {};
  }

  const entries = fs.readdirSync(testResultsDir, { withFileTypes: true });
  const errorContextMap: ErrorContextMap = {};

  for (const entry of entries) {
    if (entry.isDirectory()) {
      const errorContextPath = path.join(testResultsDir, entry.name, 'error-context.md');
      if (fs.existsSync(errorContextPath)) {
        errorContextMap[entry.name] = errorContextPath;
      }
    }
  }

  return errorContextMap;
}

function findErrorContextPath(
  suiteFile: string,
  errorContextFiles: ErrorContextMap,
): string | undefined {
  const testFileName = suiteFile.replace(/^tests\//, '').replace(/\.pw\.ts$/, '');
  for (const [dirName, contextPath] of Object.entries(errorContextFiles)) {
    if (dirName.includes(testFileName)) {
      return contextPath;
    }
  }
  return undefined;
}

function formatFailedSpec(
  spec: any,
  suite: any,
  errorContextFiles: ErrorContextMap,
  testResultsDir: string,
) {
  const errorContextPath = findErrorContextPath(suite.file, errorContextFiles);

  return {
    file: suite.file,
    title: spec.title,
    errorContextPath: errorContextPath
      ? path.relative(testResultsDir, errorContextPath)
      : undefined,
    tests: spec.tests.flatMap(
      (test: any) =>
        test.results?.filter(isFailedResult).map((result: any) => ({
          status: result.status,
          error: result.error,
          duration: result.duration,
          retry: result.retry,
        })) || [],
    ),
  };
}

export function extractFailedTests(baseDir: string = __dirname): number {
  const resultsPath = path.join(baseDir, 'test-results', 'results.json');
  const failedPath = path.join(baseDir, 'test-results', 'failed.json');
  const testResultsDir = path.join(baseDir, 'test-results');

  if (!fs.existsSync(resultsPath)) {
    console.log('No results.json found at:', resultsPath);
    return 0;
  }

  const errorContextFiles = findErrorContextFiles(testResultsDir);

  try {
    const results = JSON.parse(fs.readFileSync(resultsPath, 'utf-8'));

    const failedTests =
      results.suites?.flatMap((suite: any) =>
        getFailedSpecs(suite).map((spec: any) =>
          formatFailedSpec(spec, suite, errorContextFiles, testResultsDir),
        ),
      ) || [];

    if (failedTests.length > 0) {
      fs.writeFileSync(
        failedPath,
        JSON.stringify(
          { failedTests, timestamp: new Date().toISOString() },
          null,
          2,
        ),
      );
      console.log(`Found ${failedTests.length} failed test(s)`);
    }

    return failedTests.length;
  } catch (error) {
    console.log('Error extracting failed tests:', error);
    return 0;
  }
}

// Allow running as a script
if (require.main === module) {
  extractFailedTests();
}
