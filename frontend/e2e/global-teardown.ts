import { FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
const upload = require('../../bin/upload-file');

async function globalTeardown(config: FullConfig) {
  console.log('Running global teardown for E2E tests...');

  // Upload screenshots/videos if they exist and not in dev mode
  const dir = path.join(__dirname, '../test-results');

  if (fs.existsSync(dir) && !process.env.E2E_DEV) {
    try {
      console.log('Uploading test artifacts...');
      const files: string[] = [];

      // Recursively find all screenshot and video files
      const findFiles = (currentDir: string) => {
        const items = fs.readdirSync(currentDir);
        for (const item of items) {
          const fullPath = path.join(currentDir, item);
          const stat = fs.statSync(fullPath);
          if (stat.isDirectory()) {
            findFiles(fullPath);
          } else if (item.match(/\.(png|jpg|jpeg|mp4|webm)$/i)) {
            files.push(fullPath);
          }
        }
      };

      findFiles(dir);

      if (files.length > 0) {
        await Promise.all(files.map(f => upload(f)));
        console.log(`Uploaded ${files.length} test artifacts`);
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