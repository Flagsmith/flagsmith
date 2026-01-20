#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * Migration script to convert TestCafe tests to Playwright
 * This script provides a basic conversion - manual review and adjustment will be needed
 */

const testFiles = [
  'segment-test.ts',
  'flag-tests.ts',
  'invite-test.ts',
  'environment-test.ts',
  'project-test.ts',
  'organisation-test.ts',
  'versioning-tests.ts',
  'organisation-permission-test.ts',
  'project-permission-test.ts',
  'environment-permission-test.ts',
  'roles-test.ts'
];

function migrateTestFile(filename) {
  const inputPath = path.join(__dirname, 'tests', filename);
  const outputPath = path.join(__dirname, 'tests', filename.replace('.ts', '.pw.ts'));

  if (!fs.existsSync(inputPath)) {
    console.log(`Skipping ${filename} - file not found`);
    return;
  }

  if (fs.existsSync(outputPath)) {
    console.log(`Skipping ${filename} - Playwright version already exists`);
    return;
  }

  let content = fs.readFileSync(inputPath, 'utf8');

  // Basic replacements
  const replacements = [
    // Import statements
    [/from '\.\.\/helpers\.cafe'/g, "from '../helpers.pw'"],
    [/import { t, Selector } from 'testcafe'/g, "import { test, expect } from '@playwright/test'"],
    [/import { test, fixture } from 'testcafe'/g, "import { test } from '@playwright/test'"],

    // Test structure
    [/export default async function\s*\([^)]*\)\s*{/g, "test.describe('TestName', () => {\n  test('test description', async ({ page }) => {\n    const helpers = createHelpers(page);"],
    [/export default async function/g, "test('test description', async ({ page }) => {\n    const helpers = createHelpers(page);"],

    // Helper function calls
    [/await click\(/g, "await helpers.click("],
    [/await setText\(/g, "await helpers.setText("],
    [/await waitForElementVisible\(/g, "await helpers.waitForElementVisible("],
    [/await waitForElementNotExist\(/g, "await helpers.waitForElementNotExist("],
    [/await clickByText\(/g, "await helpers.clickByText("],
    [/await gotoFeatures\(/g, "await helpers.gotoFeatures("],
    [/await gotoSegments\(/g, "await helpers.gotoSegments("],
    [/await login\(/g, "await helpers.login("],
    [/await logout\(/g, "await helpers.logout("],
    [/await selectToggle\(/g, "await helpers.selectToggle("],

    // TestCafe specific
    [/await t\./g, "await "],
    [/Selector\(/g, "page.locator("],
    [/\.withText\(/g, ".filter({ hasText: "],
    [/\.exists/g, ""],
    [/\.ok\(/g, ".toBeVisible("],
    [/\.notOk\(/g, ".not.toBeVisible("],
    [/\.expect\(/g, "expect("],

    // Navigation
    [/await t\.navigateTo\(/g, "await page.goto("],
    [/await t\.eval\(/g, "await page.evaluate("],
    [/await t\.wait\(/g, "await page.waitForTimeout("],

    // Assertions
    [/\.eql\(/g, ".toBe("],
    [/\.contains\(/g, ".toContain("],
    [/\.typeText\(/g, ".fill("],
    [/\.click\(/g, ".click("],
    [/\.pressKey\(/g, ".press("],
    [/\.hover\(/g, ".hover("],

    // Close the function properly
    [/}\s*$/g, "  });\n});"]
  ];

  replacements.forEach(([pattern, replacement]) => {
    content = content.replace(pattern, replacement);
  });

  // Add necessary imports at the top if not present
  if (!content.includes("import { test")) {
    content = "import { test, expect } from '@playwright/test';\n" + content;
  }
  if (!content.includes("createHelpers")) {
    content = content.replace(
      /from '\.\.\/helpers\.pw'/,
      ", createHelpers from '../helpers.pw'"
    );
  }

  // Write the migrated file
  fs.writeFileSync(outputPath, content);
  console.log(`Migrated ${filename} -> ${outputPath}`);
  console.log('  Note: Manual review and adjustment required');
}

// Run migration for all test files
console.log('Starting TestCafe to Playwright migration...\n');
testFiles.forEach(migrateTestFile);

console.log('\n=================================');
console.log('Migration complete!');
console.log('IMPORTANT: The generated files need manual review and adjustment.');
console.log('Common things to check:');
console.log('  - Test descriptions and structure');
console.log('  - Async/await usage');
console.log('  - Page navigation and waits');
console.log('  - Assertions and expectations');
console.log('  - Removal of TestCafe-specific code');
console.log('=================================');