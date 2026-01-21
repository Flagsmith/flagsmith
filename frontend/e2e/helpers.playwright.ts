import { Page, expect, Locator } from '@playwright/test';
import Project from '../common/project';
import fetch from 'node-fetch';
import flagsmith from 'flagsmith/isomorphic';
import { IFlagsmith } from 'flagsmith/types';

export const LONG_TIMEOUT = 10000;

// Browser debugging - console and network logging
export const setupBrowserLogging = (page: Page) => {
  // Track console messages
  page.on('console', async (msg) => {
    const type = msg.type();
    const text = msg.text();

    // Only log errors and warnings
    if (type === 'error') {
      console.error('\n🔴 [CONSOLE ERROR]', text);
      // Try to get stack trace if available
      const args = msg.args();
      for (const arg of args) {
        try {
          const val = await arg.jsonValue();
          if (val && typeof val === 'object' && val.stack) {
            console.error('  Stack:', val.stack);
          }
        } catch (e) {
          // Ignore if we can't get the value
        }
      }
    } else if (type === 'warning') {
      // Disabled to reduce noise
      // console.warn('\n🟡 [CONSOLE WARNING]', text);
    }
  });

  // Track page errors
  page.on('pageerror', (error) => {
    console.error('\n🔴 [PAGE ERROR]', error.message);
    if (error.stack) {
      console.error('  Stack:', error.stack);
    }
  });

  // Track failed network requests
  page.on('requestfailed', (request) => {
    const url = request.url();
    const failure = request.failure();
    console.error('\n🔴 [NETWORK FAILED]', request.method(), url);
    if (failure) {
      console.error('  Error:', failure.errorText);
    }
  });

  // Track API responses with errors
  page.on('response', async (response) => {
    const url = response.url();
    const status = response.status();

    // Only log API calls (not static assets)
    if (!url.includes('/api/') && !url.includes('/e2etests/')) {
      return;
    }

    // Ignore false positive errors that are expected/harmless
    if (status === 404 && url.includes('/usage-data/')) {
      // usage-data 404s are expected for new orgs without billing
      return;
    }
    if (status === 404 && url.includes('/list-change-requests/')) {
      // Change requests is an enterprise feature, 404s are expected in OSS
      return;
    }
    if (status === 400 && url.includes('/organisations/undefined/')) {
      // Happens during initial page load before org is selected
      return;
    }
    if (status === 403) {
      // These 403s are expected for non-admin users
      if (url.includes('/get-subscription-metadata/') ||
          url.includes('/usage-data/') ||
          url.includes('/invite-links/')) {
        return;
      }
    }
    if (status === 429 && url.includes('/usage-data/')) {
      // Usage data endpoint has rate limiting, throttling is expected
      return;
    }

    // Log throttling, rate limiting, and server errors
    if (status === 429) {
      console.error('\n🔴 [API THROTTLED]', response.request().method(), url);
      try {
        const body = await response.text();
        console.error('  Response:', body);
      } catch (e) {
        // Ignore if we can't read the body
      }
    } else if (status >= 400 && status < 500) {
      console.error(`\n🔴 [API CLIENT ERROR ${status}]`, response.request().method(), url);
      try {
        const body = await response.text();
        console.error('  Response:', body);
      } catch (e) {
        // Ignore if we can't read the body
      }
    } else if (status >= 500) {
      console.error(`\n🔴 [API SERVER ERROR ${status}]`, response.request().method(), url);
      try {
        const body = await response.text();
        console.error('  Response:', body);
      } catch (e) {
        // Ignore if we can't read the body
      }
    }
  });

  console.log('✅ Browser logging enabled (console errors, network failures, API errors)');
};

export const byId = (id: string) => `[data-test="${id}"]`;

export type MultiVariate = { value: string; weight: number };

export type Rule = {
  name: string;
  operator: string;
  value: string | number | boolean;
  ors?: Rule[];
};

// Initialize Flagsmith once
const initProm = flagsmith.init({
  api: Project.flagsmithClientAPI,
  environmentID: Project.flagsmith,
  fetch,
});

export const getFlagsmith = async function (): Promise<IFlagsmith> {
  await initProm;
  return flagsmith as IFlagsmith;
};

// Logging functions
let currentSection = '';

export const log = (section?: string, message?: string) => {
  if (section) {
    currentSection = section;
    console.log(`\n[${section}]`);
  }
  if (message) {
    console.log(message);
  }
};

export const logUsingLastSection = (message: string) => {
  if (currentSection) {
    console.log(`[${currentSection}] ${message}`);
  } else {
    console.log(message);
  }
};

// API Request logger for Playwright
export const checkApiRequest = (
  urlPattern: RegExp,
  method: 'get' | 'post' | 'put' | 'patch' | 'delete',
) => {
  const requests: any[] = [];

  return {
    requests,
    clear: () => {
      requests.length = 0;
    },
  };
};

// Page-based helper functions
export class E2EHelpers {
  constructor(private page: Page) {}

  async isElementExists(selector: string): Promise<boolean> {
    return await this.page.locator(byId(selector)).count() > 0;
  }

  async setText(selector: string, text: string) {
    logUsingLastSection(`Set text ${selector} : ${text}`);
    const element = this.page.locator(selector).first();
    await element.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await element.clear();
    if (text) {
      await element.fill(text);
    }
  }

  async waitForElementVisible(selector: string) {
    logUsingLastSection(`Waiting element visible ${selector}`);
    await this.page.locator(selector).first().waitFor({
      state: 'visible',
      timeout: LONG_TIMEOUT
    });
  }

  async waitForElementNotClickable(selector: string) {
    logUsingLastSection(`Waiting element not clickable ${selector}`);
    const element = this.page.locator(selector).first();
    await element.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await expect(element).toBeDisabled();
  }

  async waitForElementClickable(selector: string) {
    logUsingLastSection(`Waiting element clickable ${selector}`);
    const element = this.page.locator(selector).first();
    await element.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await expect(element).toBeEnabled();
  }

  async clickSegmentByName(name: string) {
    const selector = '[data-test^="segment-"][data-test$="-name"]';
    const element = this.page.locator(selector).filter({ hasText: name });
    await element.scrollIntoViewIfNeeded();
    await expect(element).toBeVisible({ timeout: LONG_TIMEOUT });
    await element.click();
  }

  async waitForElementNotExist(selector: string) {
    logUsingLastSection(`Waiting element not exist ${selector}`);
    await expect(this.page.locator(selector)).toHaveCount(0, { timeout: 10000 });
  }

  async gotoFeatures() {
    await this.click('#features-link');
    await this.waitForElementVisible('#show-create-feature-btn');
  }

  async click(selector: string) {
    await this.waitForElementVisible(selector);
    const element = this.page.locator(selector).first();
    await element.scrollIntoViewIfNeeded();
    await expect(element).toBeEnabled({ timeout: LONG_TIMEOUT });
    await element.hover();
    await element.click();
  }

  async clickByText(text: string, element: string = 'button') {
    logUsingLastSection(`Click by text ${text} ${element}`);
    const selector = this.page.locator(element).filter({ hasText: text });
    await selector.scrollIntoViewIfNeeded();
    await expect(selector).toBeEnabled({ timeout: 5000 });
    await selector.hover();
    await selector.click();
  }

  async gotoSegments() {
    await this.click('#segments-link');
    await this.waitForElementVisible(byId('show-create-segment-btn'));
  }

  async getFeatureValue(name: string, projectId: string): Promise<string> {
    logUsingLastSection('Getting feature value for ' + name);
    const url = `${Project.api}projects/${projectId}/features/?page_size=999&search=${name}&environment=`;
    const token = (await this.getCookie('.Admin.Token')) || '';
    const options = {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'x-e2e-token': process.env.E2E_TEST_TOKEN || '',
        ...(token && { Authorization: `Token ${token}` }),
      },
      method: 'GET',
    };
    const res = await fetch(url, options);
    const json = await res.json();
    const feature = json.results.find(
      (v: any) => v.name.toLowerCase() === name.toLowerCase(),
    );
    return feature?.initial_value;
  }

  async getCookie(name: string): Promise<string | undefined> {
    const cookies = await this.page.context().cookies();
    const cookie = cookies.find(c => c.name === name);
    return cookie?.value;
  }

  async setCookie(name: string, value: string, domain = 'localhost') {
    await this.page.context().addCookies([{
      name,
      value,
      domain,
      path: '/',
    }]);
  }

  async login(
    email: string = process.env.E2E_USER || '',
    password: string = process.env.E2E_PASS || '',
  ) {
    await this.page.goto('/login');
    await this.setText('[name="email"]', email);
    await this.setText('[name="password"]', password);
    await this.click('#login-btn');
    // Wait for navigation to complete
    await this.page.waitForURL(/\/organisation\/\d+/, { timeout: LONG_TIMEOUT });
    // Wait for the project manage widget to be present and projects to load
    await this.waitForElementVisible('#project-manage-widget');
    // Wait for loading to complete - either project list or no projects message appears
    await this.page.waitForFunction(() => {
      const widget = document.querySelector('#project-manage-widget');
      if (!widget) return false;
      // Check if loader is gone and content is visible
      const hasLoader = widget.querySelector('.centered-container .loader');
      return !hasLoader;
    }, { timeout: LONG_TIMEOUT });
  }

  async logout() {
    try {
      await this.click('#account-settings-link');
      await this.click('#logout-link');
      await this.waitForElementVisible('#login-page');
      await this.page.waitForTimeout(500);
    } catch (e) {
      console.log('Could not log out:', e);
    }
  }

  // Additional helper methods for common operations
  async selectToggle(selector: string, value: boolean = true) {
    const element = this.page.locator(selector).first();
    await element.waitFor({ state: 'visible' });
    const isChecked = await element.isChecked();
    if (isChecked !== value) {
      await element.click();
    }
  }

  async waitForUrl(urlPattern: string | RegExp, timeout: number = LONG_TIMEOUT) {
    await this.page.waitForURL(urlPattern, { timeout });
  }

  async takeScreenshot(name: string) {
    await this.page.screenshot({ path: `test-results/screenshots/${name}.png` });
  }

  async waitAndClick(selector: string) {
    await this.waitForElementVisible(selector);
    await this.click(selector);
  }

  async assertTextContent(selector: string, expectedText: string) {
    await expect(this.page.locator(selector)).toContainText(expectedText);
  }

  async assertElementExists(selector: string) {
    await expect(this.page.locator(selector)).toHaveCount(1);
  }

  async assertElementNotExists(selector: string) {
    await expect(this.page.locator(selector)).toHaveCount(0);
  }

  async waitForApiResponse(urlPattern: string | RegExp) {
    return this.page.waitForResponse(urlPattern);
  }

  // Console and error logging
  async getConsoleMessages() {
    const messages: string[] = [];
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        messages.push(msg.text());
      }
    });
    return messages;
  }

  // Add client script for error logging
  async addErrorLogging() {
    await this.page.addInitScript(() => {
      window.addEventListener('error', (e) => {
        console.error('Page error:', e.message, e.filename, e.lineno, e.colno);
      });
      window.addEventListener('unhandledrejection', (e) => {
        console.error('Unhandled promise rejection:', e.reason);
      });
    });
  }
}

// Export a factory function to create helpers for a page
export function createHelpers(page: Page): E2EHelpers {
  return new E2EHelpers(page);
}

// ============================================================================
// Standalone helper functions
// ============================================================================

// Check if an element exists
export const isElementExists = async (page: Page, selector: string): Promise<boolean> => {
  return await page.locator(byId(selector)).count() > 0;
};

// Set text in an input field
export const setText = async (page: Page, selector: string, text: string) => {
  logUsingLastSection(`Set text ${selector} : ${text}`);
  const element = page.locator(selector);
  await element.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
  await element.clear();
  // Small wait after clearing to let React state update
  await page.waitForTimeout(50);
  if (text) {
    await element.fill(text);
    // Small wait after filling to let React state update
    await page.waitForTimeout(50);
  }
};

// Wait for an element to be visible
export const waitForElementVisible = async (page: Page, selector: string) => {
  logUsingLastSection(`Waiting element visible ${selector}`);
  await page.locator(selector).first().waitFor({
    state: 'visible',
    timeout: LONG_TIMEOUT
  });
};

// Wait for an element to not be clickable (disabled)
export const waitForElementNotClickable = async (page: Page, selector: string) => {
  logUsingLastSection(`Waiting element not clickable ${selector}`);
  const element = page.locator(selector).first();
  await element.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
  await expect(element).toBeDisabled({ timeout: LONG_TIMEOUT });
};

// Wait for an element to be clickable (enabled)
export const waitForElementClickable = async (page: Page, selector: string) => {
  logUsingLastSection(`Waiting element clickable ${selector}`);
  const element = page.locator(selector).first();
  await element.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
  await expect(element).toBeEnabled({ timeout: LONG_TIMEOUT });
};

// Click a segment by name
export const clickSegmentByName = async (page: Page, name: string) => {
  const selector = '[data-test^="segment-"][data-test$="-name"]';
  const element = page.locator(selector).filter({ hasText: name });
  await element.scrollIntoViewIfNeeded();
  await expect(element).toBeVisible({ timeout: LONG_TIMEOUT });
  await element.click();
};

// Wait for an element to not exist
export const waitForElementNotExist = async (page: Page, selector: string) => {
  logUsingLastSection(`Waiting element not exist ${selector}`);
  await expect(page.locator(selector)).toHaveCount(0, { timeout: 10000 });
};

// Navigate to features page
export const gotoFeatures = async (page: Page) => {
  await click(page, '#features-link');
  await waitForElementVisible(page, '#show-create-feature-btn');
};

// Click an element
export const click = async (page: Page, selector: string) => {
  await waitForElementVisible(page, selector);
  const element = page.locator(selector).first();
  await element.scrollIntoViewIfNeeded();
  await expect(element).toBeEnabled({ timeout: LONG_TIMEOUT });
  await element.hover();
  await element.click();
};

// Click by text content
export const clickByText = async (page: Page, text: string, element: string = 'button') => {
  logUsingLastSection(`Click by text ${text} ${element}`);
  const selector = page.locator(element).filter({ hasText: text });
  await selector.scrollIntoViewIfNeeded();
  await expect(selector).toBeEnabled({ timeout: 5000 });
  await selector.hover();
  await selector.click();
};

// Navigate to segments page
export const gotoSegments = async (page: Page) => {
  await click(page, '#segments-link');
  await waitForElementVisible(page, byId('show-create-segment-btn'));
};

// Create a role
export const createRole = async (
  page: Page,
  roleName: string,
  index: number,
  users: number[],
) => {
  await click(page, byId('tab-item-roles'));
  await click(page, byId('create-role'));
  await setText(page, byId('role-name'), roleName);
  await click(page, byId('save-role'));
  await click(page, byId(`role-${index}`));
  await click(page, byId('members-tab'));
  await click(page, byId('assigned-users'));
  for (const userId of users) {
    await click(page, byId(`assignees-list-item-${userId}`));
  }
  await closeModal(page);
};

// Navigate to traits page
export const gotoTraits = async (page: Page) => {
  await click(page, '#features-link');
  await click(page, '#users-link');
  await click(page, byId('user-item-0'));
  await waitForElementVisible(page, '#add-trait');
};

// Create a trait
export const createTrait = async (
  page: Page,
  index: number,
  id: string,
  value: string | boolean | number,
) => {
  await click(page, '#add-trait');
  await waitForElementVisible(page, '#create-trait-modal');
  await setText(page, '[name="traitID"]', id);
  await setText(page, '[name="traitValue"]', `${value}`);
  await click(page, '#create-trait-btn');
  await page.waitForTimeout(2000);
  await page.reload();
  await waitForElementVisible(page, byId(`user-trait-value-${index}`));
  const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
  await assertTextContent(page, byId(`user-trait-value-${index}`), expectedValue);
};

// Delete a trait
export const deleteTrait = async (page: Page, index: number) => {
  await click(page, byId(`delete-user-trait-${index}`));
  await click(page, '#confirm-btn-yes');
  await waitForElementNotExist(page, byId(`user-trait-${index}`));
};

// View a feature by index
export const viewFeature = async (page: Page, index: number) => {
  await click(page, byId(`feature-item-${index}`));
  await waitForElementVisible(page, '#create-feature-modal');
};

// Add segment override configuration
export const addSegmentOverrideConfig = async (
  page: Page,
  index: number,
  value: string | boolean | number,
  selectionIndex: number = 0,
) => {
  // Check if dropdown is already visible, only click if it's not
  const dropdownSelector = byId(`select-segment-option-${selectionIndex}`);
  const isDropdownVisible = await page.locator(dropdownSelector).isVisible().catch(() => false);

  if (!isDropdownVisible) {
    await click(page, byId('segment_overrides'));
  }

  await click(page, dropdownSelector);
  await waitForElementVisible(page, byId(`segment-override-value-${index}`));
  await setText(page, byId(`segment-override-value-${index}`), `${value}`);
  await click(page, byId(`segment-override-toggle-${index}`));
};

// Add segment override
export const addSegmentOverride = async (
  page: Page,
  index: number,
  value: string | boolean | number,
  selectionIndex: number = 0,
  mvs: MultiVariate[] = [],
) => {
  // Check if dropdown is already visible, only click if it's not
  const dropdownSelector = byId(`select-segment-option-${selectionIndex}`);
  const isDropdownVisible = await page.locator(dropdownSelector).isVisible().catch(() => false);

  if (!isDropdownVisible) {
    await click(page, byId('segment_overrides'));
  }

  await click(page, dropdownSelector);
  await waitForElementVisible(page, byId(`segment-override-value-${index}`));

  // Set multivariate weights first before enabling the switch
  if (mvs && mvs.length > 0) {
    // Set weights sequentially instead of in parallel to avoid race conditions
    for (const v of mvs) {
      await setText(
        page,
        `.segment-overrides ${byId(`featureVariationWeight${v.value}`)}`,
        `${v.weight}`,
      );
      // Small wait between each weight change
      await page.waitForTimeout(100);
    }
    // Wait longer for React state to fully update after all weight changes
    await page.waitForTimeout(500);
  }

  // For boolean flags, simply click the toggle if the value is truthy
  // This matches the TestCafe behavior exactly
  if (value) {
    await click(page, byId(`segment-override-toggle-${index}`));
  }
};

// Save feature
export const saveFeature = async (page: Page) => {
  await click(page, '#update-feature-btn');
  await waitForElementVisible(page, '.toast-message');
  await waitForElementNotExist(page, '.toast-message');
  await closeModal(page);
  await waitForElementNotExist(page, '#create-feature-modal');
};

// Save feature segments
export const saveFeatureSegments = async (page: Page) => {
  await click(page, '#update-feature-segments-btn');
  // Wait for success message to appear indicating save completed
  await page.waitForSelector('.toast-message', { state: 'visible', timeout: 10000 });
  // Wait for toast to disappear
  await page.waitForSelector('.toast-message', { state: 'hidden', timeout: 10000 });
  await closeModal(page);
  await waitForElementNotExist(page, '#create-feature-modal');
};

// Create an environment
export const createEnvironment = async (page: Page, name: string) => {
  await setText(page, '[name="envName"]', name);
  await click(page, '#create-env-btn');
  await waitForElementVisible(
    page,
    byId(`switch-environment-${name.toLowerCase()}-active`),
  );
};

// Navigate to a user
export const goToUser = async (page: Page, index: number) => {
  await click(page, '#features-link');
  await click(page, '#users-link');
  await click(page, byId(`user-item-${index}`));
};

// Navigate to a feature
export const gotoFeature = async (page: Page, index: number) => {
  await click(page, byId(`feature-item-${index}`));
  await waitForElementVisible(page, '#create-feature-modal');
};

// Set segment override index
export const setSegmentOverrideIndex = async (
  page: Page,
  index: number,
  newIndex: number,
) => {
  await click(page, byId('segment_overrides'));
  await setText(page, byId(`sort-${index}`), `${newIndex}`);
};

// Assert input value
export const assertInputValue = async (page: Page, selector: string, v: string) => {
  await expect(page.locator(selector)).toHaveValue(v);
};

// Assert text content
export const assertTextContent = async (page: Page, selector: string, v: string) => {
  await expect(page.locator(selector)).toHaveText(v);
};

// Assert text content contains
export const assertTextContentContains = async (page: Page, selector: string, v: string) => {
  await expect(page.locator(selector)).toContainText(v);
};

// Get text from element
export const getText = async (page: Page, selector: string): Promise<string> => {
  return await page.locator(selector).innerText();
};

// Parse try it results
export const parseTryItResults = async (page: Page): Promise<Record<string, any>> => {
  const text = await getText(page, '#try-it-results');
  try {
    return JSON.parse(text);
  } catch (e) {
    throw new Error('Try it results are not valid JSON');
  }
};

// Clone a segment
export const cloneSegment = async (page: Page, index: number, name: string) => {
  await click(page, byId(`segment-action-${index}`));
  await click(page, byId(`segment-clone-${index}`));
  await setText(page, '[name="clone-segment-name"]', name);
  await click(page, '#confirm-clone-segment-btn');
  await waitForElementVisible(page, byId(`segment-${index + 1}-name`));
};

// Delete segment from the segment page
export const deleteSegmentFromPage = async (page: Page, name: string) => {
  await click(page, byId('remove-segment-btn'));
  await setText(page, '[name="confirm-segment-name"]', name);
  await click(page, '#confirm-remove-segment-btn');
  await waitForElementVisible(page, byId('show-create-segment-btn'));
};

// Delete a segment
export const deleteSegment = async (page: Page, index: number, name: string) => {
  await click(page, byId(`segment-action-${index}`));
  await click(page, byId(`segment-remove-${index}`));
  await setText(page, '[name="confirm-segment-name"]', name);
  await click(page, '#confirm-remove-segment-btn');
  await waitForElementNotExist(page, `remove-segment-btn-${index}`);
};

// Login
export const login = async (page: Page, email: string, password: string) => {
  await setText(page, '[name="email"]', email);
  await setText(page, '[name="password"]', password);
  await click(page, '#login-btn');
  // Wait for navigation to complete
  await page.waitForURL(/\/organisation\/\d+/, { timeout: LONG_TIMEOUT });
  // Wait for the project manage widget to be present and projects to load
  await waitForElementVisible(page, '#project-manage-widget');
  // Wait for loading to complete - either project list or no projects message appears
  await page.waitForFunction(() => {
    const widget = document.querySelector('#project-manage-widget');
    if (!widget) return false;
    // Check if loader is gone and content is visible
    const hasLoader = widget.querySelector('.centered-container .loader');
    return !hasLoader;
  }, { timeout: LONG_TIMEOUT });
};

// Logout
export const logout = async (page: Page) => {
  await click(page, '#account-settings-link');
  await click(page, '#logout-link');
  await waitForElementVisible(page, '#login-page');
  await page.waitForTimeout(500);
};

// Navigate to feature versions
export const goToFeatureVersions = async (page: Page, featureIndex: number) => {
  await gotoFeature(page, featureIndex);
  if (await isElementExists(page, 'change-history')) {
    await click(page, byId('change-history'));
  } else {
    await click(page, byId('tabs-overflow-button'));
    await click(page, byId('change-history'));
  }
};

// Compare version
export const compareVersion = async (
  page: Page,
  featureIndex: number,
  versionIndex: number,
  compareOption: 'LIVE' | 'PREVIOUS' | null,
  oldEnabled: boolean,
  newEnabled: boolean,
  oldValue?: any,
  newValue?: any,
) => {
  await goToFeatureVersions(page, featureIndex);
  await click(page, byId(`history-item-${versionIndex}-compare`));
  if (compareOption === 'LIVE') {
    await click(page, byId(`history-item-${versionIndex}-compare-live`));
  } else if (compareOption === 'PREVIOUS') {
    await click(page, byId(`history-item-${versionIndex}-compare-previous`));
  }

  // Wait for comparison modal to fully load data
  await page.waitForTimeout(2000);

  // Use .first() to handle cases where multiple comparison modals might exist in DOM
  await expect(page.locator(byId('old-enabled')).first()).toHaveText(`${oldEnabled}`);
  await expect(page.locator(byId('new-enabled')).first()).toHaveText(`${newEnabled}`);
  if (oldValue !== undefined) {
    // When value is null, the UI shows an empty string, not the text "null"
    const expectedOldValue = oldValue === null ? '' : `${oldValue}`;
    await expect(page.locator(byId('old-value')).first()).toHaveText(expectedOldValue);
  }
  if (newValue !== undefined) {
    // When value is null, the UI shows an empty string, not the text "null"
    const expectedNewValue = newValue === null ? '' : `${newValue}`;
    await expect(page.locator(byId('new-value')).first()).toHaveText(expectedNewValue);
  }
  await closeModal(page);
};

// Assert number of versions
export const assertNumberOfVersions = async (
  page: Page,
  index: number,
  versions: number,
) => {
  await goToFeatureVersions(page, index);
  await waitForElementVisible(page, byId(`history-item-${versions - 2}-compare`));
  await closeModal(page);
};

// Create a remote config (feature with value)
export const createRemoteConfig = async (
  page: Page,
  index: number,
  name: string,
  value: string | number | boolean,
  description: string = 'description',
  defaultOff?: boolean,
  mvs: MultiVariate[] = [],
) => {
  const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
  await gotoFeatures(page);
  await click(page, '#show-create-feature-btn');
  await setText(page, byId('featureID'), name);
  await setText(page, byId('featureValue'), `${value}`);
  await setText(page, byId('featureDesc'), description);
  if (!defaultOff) {
    await click(page, byId('toggle-feature-button'));
  }
  for (let i = 0; i < mvs.length; i++) {
    const v = mvs[i];
    await click(page, byId('add-variation'));
    // Wait for the new variation row to appear
    await page.waitForTimeout(200);
    await setText(page, byId(`featureVariationValue${i}`), v.value);
    await setText(page, byId(`featureVariationWeight${v.value}`), `${v.weight}`);
    // Small wait between each variation to let React state update
    await page.waitForTimeout(100);
  }
  // Wait for form validation to complete after all variations added
  if (mvs.length > 0) {
    await page.waitForTimeout(500);
  }
  await click(page, byId('create-feature-btn'));
  await waitForElementVisible(page, byId(`feature-value-${index}`));
  await assertTextContent(page, byId(`feature-value-${index}`), expectedValue);
  await closeModal(page);
};

// Create organisation and project
export const createOrganisationAndProject = async (
  page: Page,
  organisationName: string,
  projectName: string,
) => {
  log('Create Organisation');
  await click(page, byId('home-link'));
  await click(page, byId('create-organisation-btn'));
  await setText(page, '[name="orgName"]', organisationName);
  await click(page, '#create-org-btn');
  // Wait for navigation to projects page and project list to load
  await page.waitForURL(/\/organisation\/\d+/, { timeout: LONG_TIMEOUT });
  await waitForElementVisible(page, byId('project-manage-widget'));
  // Wait for loading to complete
  await page.waitForFunction(() => {
    const widget = document.querySelector('#project-manage-widget');
    if (!widget) return false;
    const hasLoader = widget.querySelector('.centered-container .loader');
    return !hasLoader;
  }, { timeout: LONG_TIMEOUT });

  log('Create Project');
  await click(page, '.btn-project-create');
  await setText(page, byId('projectName'), projectName);
  await click(page, byId('create-project-btn'));
  await waitForElementVisible(page, byId('features-page'));
};

// Edit remote config
export const editRemoteConfig = async (
  page: Page,
  index: number,
  value: string | number | boolean,
  toggleFeature: boolean = false,
  mvs: MultiVariate[] = [],
) => {
  const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
  await gotoFeatures(page);
  await click(page, byId(`feature-item-${index}`));

  // Change the value field first (if needed) to match TestCafe behavior
  if (value !== '') {
    await setText(page, byId('featureValue'), `${value}`);
  }

  // Change multivariate weights - must be done after value field to avoid state conflicts
  if (mvs.length > 0) {
    // Wait after value field change before modifying weights
    await page.waitForTimeout(500);

    for (const v of mvs) {
      const selector = byId(`featureVariationWeight${v.value}`);
      // Wait for the weight input to be visible before trying to interact with it
      await waitForElementVisible(page, selector);
      const input = page.locator(selector);
      await input.clear();
      await page.waitForTimeout(100);
      await input.fill(`${v.weight}`);
      await page.waitForTimeout(100);
      // Trigger blur to force validation
      await input.blur();
      // Wait between each weight change to let React state and validation update
      await page.waitForTimeout(500);
    }
  }

  if (toggleFeature) {
    await click(page, byId('toggle-feature-button'));
  }

  // Wait for the update button to become enabled after all changes
  if (mvs.length > 0 || value !== '') {
    // Use a long fixed timeout for form validation to complete
    await page.waitForTimeout(1500);
  }

  // Use button text to avoid strict mode violation (multiple buttons with same ID)
  await click(page, 'button:has-text("Update Feature Value")');
  if (value) {
    await waitForElementVisible(page, byId(`feature-value-${index}`));
    await assertTextContent(page, byId(`feature-value-${index}`), expectedValue);
  }
  await closeModal(page);
};

// Close modal
export const closeModal = async (page: Page) => {
  log('Close Modal');
  await page.mouse.click(50, 50);
};

// Create a feature (flag)
export const createFeature = async (
  page: Page,
  index: number,
  name: string,
  value?: string | boolean | number,
  description: string = 'description',
) => {
  await gotoFeatures(page);
  await click(page, '#show-create-feature-btn');
  await setText(page, byId('featureID'), name);
  await setText(page, byId('featureDesc'), description);
  if (value) {
    await click(page, byId('toggle-feature-button'));
  }
  await click(page, byId('create-feature-btn'));
  await waitForElementVisible(page, byId(`feature-item-${index}`));
  await closeModal(page);
};

// Delete a feature
export const deleteFeature = async (page: Page, index: number, name: string) => {
  await click(page, byId(`feature-action-${index}`));
  await waitForElementVisible(page, byId(`feature-remove-${index}`));
  await click(page, byId(`feature-remove-${index}`));
  await setText(page, '[name="confirm-feature-name"]', name);
  await click(page, '#confirm-remove-feature-btn');
  await waitForElementNotExist(page, `feature-remove-${index}`);
};

// Toggle a feature on/off
export const toggleFeature = async (page: Page, index: number, toValue: boolean) => {
  await click(page, byId(`feature-switch-${index}-${toValue ? 'off' : 'on'}`));
  await click(page, '#confirm-toggle-feature-btn');
  await waitForElementVisible(
    page,
    byId(`feature-switch-${index}-${toValue ? 'on' : 'off'}`),
  );
};

// Set user permissions
export const setUserPermissions = async (page: Page, index: number, toValue: boolean) => {
  await click(page, byId(`feature-switch-${index}${toValue ? '-off' : 'on'}`));
  await click(page, '#confirm-toggle-feature-btn');
  await waitForElementVisible(
    page,
    byId(`feature-switch-${index}${toValue ? '-on' : 'off'}`),
  );
};

// Set segment rule
export const setSegmentRule = async (
  page: Page,
  ruleIndex: number,
  orIndex: number,
  name: string,
  operator: string,
  value: string | number | boolean,
) => {
  await setText(page, byId(`rule-${ruleIndex}-property-${orIndex}`), name);
  if (operator) {
    await setText(page, byId(`rule-${ruleIndex}-operator-${orIndex}`), operator);
  }
  await setText(page, byId(`rule-${ruleIndex}-value-${orIndex}`), `${value}`);
};

// Create a segment
export const createSegment = async (
  page: Page,
  index: number,
  id: string,
  rules?: Rule[],
) => {
  await click(page, byId('show-create-segment-btn'));
  await setText(page, byId('segmentID'), id);
  if (rules && rules.length > 0) {
    for (let x = 0; x < rules.length; x++) {
      const rule = rules[x];
      if (x > 0) {
        // eslint-disable-next-line no-await-in-loop
        await click(page, byId('add-rule'));
        // eslint-disable-next-line no-await-in-loop
        // Wait for the new rule row to appear before trying to interact with it
        await waitForElementVisible(page, byId(`rule-${x}-property-0`));
      }
      // eslint-disable-next-line no-await-in-loop
      await setSegmentRule(page, x, 0, rule.name, rule.operator, rule.value);
      if (rule.ors) {
        for (let orIndex = 0; orIndex < rule.ors.length; orIndex++) {
          const or = rule.ors[orIndex];
          // eslint-disable-next-line no-await-in-loop
          await click(page, byId(`rule-${x}-or`));
          // eslint-disable-next-line no-await-in-loop
          // Wait for the new OR row to appear before trying to interact with it
          await waitForElementVisible(page, byId(`rule-${x}-property-${orIndex + 1}`));
          // eslint-disable-next-line no-await-in-loop
          await setSegmentRule(page, x, orIndex + 1, or.name, or.operator, or.value);
        }
      }
    }
  }

  // Create
  await click(page, byId('create-segment'));
  await waitForElementVisible(page, byId(`segment-${index}-name`));
  await assertTextContent(page, byId(`segment-${index}-name`), id);
};

// Wait and refresh
export const waitAndRefresh = async (page: Page, waitFor: number = 3000) => {
  logUsingLastSection(`Waiting for ${waitFor}ms, then refreshing.`);
  await page.waitForTimeout(waitFor);
  await page.reload();
};

// Refresh until element is visible
export const refreshUntilElementVisible = async (
  page: Page,
  selector: string,
  maxRetries: number = 20,
) => {
  const element = page.locator(selector);
  let retries = 0;
  while (retries < maxRetries) {
    const isVisible = await element.isVisible().catch(() => false);
    if (isVisible) {
      break;
    }
    await page.reload();
    await page.waitForTimeout(3000);
    retries++;
  }
  await element.scrollIntoViewIfNeeded();
};

// Permission map
const permissionsMap = {
  'APPROVE_CHANGE_REQUEST': 'environment',
  'CREATE_CHANGE_REQUEST': 'environment',
  'CREATE_ENVIRONMENT': 'project',
  'CREATE_FEATURE': 'project',
  'CREATE_PROJECT': 'organisation',
  'DELETE_FEATURE': 'project',
  'MANAGE_IDENTITIES': 'environment',
  'MANAGE_SEGMENTS': 'project',
  'MANAGE_SEGMENT_OVERRIDES': 'environment',
  'MANAGE_TAGS': 'project',
  'MANAGE_USERS': 'organisation',
  'MANAGE_USER_GROUPS': 'organisation',
  'UPDATE_FEATURE_STATE': 'environment',
  'VIEW_AUDIT_LOG': 'project',
  'VIEW_ENVIRONMENT': 'environment',
  'VIEW_IDENTITIES': 'environment',
  'VIEW_PROJECT': 'project',
} as const;

// Set user permission
export const setUserPermission = async (
  page: Page,
  email: string,
  permission: keyof typeof permissionsMap | 'ADMIN',
  entityName: string | null,
  entityLevel?: 'project' | 'environment' | 'organisation',
  parentName?: string,
) => {
  await click(page, byId('users-and-permissions'));
  await click(page, byId(`user-${email}`));
  const level = permissionsMap[permission] || entityLevel;
  await click(page, byId(`${level}-permissions-tab`));
  if (parentName) {
    await clickByText(page, parentName, 'a');
  }
  if (entityName) {
    await click(page, byId(`permissions-${entityName.toLowerCase()}`));
  }
  if (permission === 'ADMIN') {
    await click(page, byId(`admin-switch-${level}`));
  } else {
    await click(page, byId(`permission-switch-${permission}`));
  }
  await closeModal(page);
};