import {
  Reporter,
  FullConfig,
  Suite,
  TestCase,
  TestResult,
  FullResult,
} from '@playwright/test/reporter';
import * as fs from 'fs';
import * as path from 'path';

class FailedTestsReporter implements Reporter {
  private failedTests: Array<{
    file: string;
    title: string;
    tests: Array<{
      status: string;
      error: any;
      duration: number;
      retry: number;
    }>;
  }> = [];

  onBegin(config: FullConfig, suite: Suite) {
    console.log('Starting E2E tests');
  }

  onTestEnd(test: TestCase, result: TestResult) {
    if (result.status === 'failed' || result.status === 'timedOut') {
      const specFile = path.relative(
        path.join(__dirname, '..'),
        test.location.file,
      );

      let failedSpec = this.failedTests.find((f) => f.file === specFile);
      if (!failedSpec) {
        failedSpec = {
          file: specFile,
          title: test.title,
          tests: [],
        };
        this.failedTests.push(failedSpec);
      }

      failedSpec.tests.push({
        status: result.status,
        error: result.error,
        duration: result.duration,
        retry: result.retry,
      });
    }
  }

  async onEnd(result: FullResult) {
    const failedCount = this.failedTests.length;

    if (failedCount > 0) {
      const failedPath = path.join(__dirname, 'test-results', 'failed.json');
      fs.writeFileSync(
        failedPath,
        JSON.stringify(
          { failedTests: this.failedTests, timestamp: new Date().toISOString() },
          null,
          2,
        ),
      );
      console.log(`Found ${failedCount} failed test(s)`);
    }

    console.log('E2E tests completed');
  }
}

export default FailedTestsReporter;
