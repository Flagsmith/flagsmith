import { FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import * as archiver from 'archiver';
import { extractFailedTests } from './extract-failed-tests';

let upload: ((file: string) => Promise<void>) | null = null;
try {
  upload = require('../bin/upload-file');
} catch (e) {
  console.log('Upload module not available:', e.message);
  // upload-file module not available, will skip uploading
}

async function zipDirectory(sourceDir: string, outPath: string): Promise<void> {
  // @ts-ignore
  const archive = archiver('zip', { zlib: { level: 9 } });
  const stream = fs.createWriteStream(outPath);

  return new Promise((resolve, reject) => {
    archive
      .directory(sourceDir, false)
      .on('error', err => reject(err))
      .pipe(stream);

    stream.on('close', () => resolve());
    archive.finalize();
  });
}

async function globalTeardown(config: FullConfig) {
  console.log('Running global teardown for E2E tests...');

  // Extract failed tests to a smaller JSON file for easier debugging
  extractFailedTests(__dirname);

  // Upload screenshots/videos if they exist and not in dev mode
  const dir = path.join(__dirname, 'test-results');

  if (fs.existsSync(dir) && !process.env.E2E_DEV) {
    try {
      console.log('Uploading test artifacts...');
      const files: string[] = [];

      // Recursively find only failed test artifacts
      const findFiles = (currentDir: string) => {
        const items = fs.readdirSync(currentDir);
        for (const item of items) {
          const fullPath = path.join(currentDir, item);
          const stat = fs.statSync(fullPath);
          if (stat.isDirectory()) {
            findFiles(fullPath);
          } else if (item.match(/\.(png|jpg|jpeg|mp4|webm)$/i)) {
            // Only upload artifacts from failed tests
            if (fullPath.includes('test-failed')) {
              files.push(fullPath);
            }
          }
        }
      };

      findFiles(dir);

      if (files.length > 0 && upload) {
        await Promise.all(files.map(f => upload!(f)));
        console.log(`Uploaded ${files.length} test artifacts`);
      } else if (files.length > 0) {
        console.log(`Found ${files.length} test artifacts but upload module not available`);
      }

      // Upload HTML report if it exists
      const reportDir = path.join(__dirname, 'playwright-report');
      if (fs.existsSync(reportDir) && upload) {
        try {
          console.log('Zipping Playwright HTML report...');
          const zipPath = path.join(__dirname, 'playwright-report.zip');
          await zipDirectory(reportDir, zipPath);
          console.log('Uploading Playwright HTML report...');
          await upload(zipPath);
          console.log('Uploaded Playwright HTML report');
          // Clean up zip file
          fs.unlinkSync(zipPath);
        } catch (e) {
          console.log('Error uploading HTML report:', e);
        }
      }
    } catch (e) {
      console.log('Error uploading files:', e);
    }
  } else {
    console.log('No files to upload');
  }

  console.log('E2E tests completed');
}

export default globalTeardown;
