import { Page, expect } from '@playwright/test';
import Project from '../common/project';
import fetch from 'node-fetch';
import flagsmith from 'flagsmith/isomorphic';
import { IFlagsmith } from 'flagsmith/types';

export const LONG_TIMEOUT = 20000;

// Map of status codes to URL patterns that should be ignored in logs
const IGNORE_RESPONSE_ERRORS: Record<number, string[]> = {
  404: [
    '/usage-data/', // Expected for new orgs without billing
    '/list-change-requests/', // Enterprise feature, expected in OSS
    '/change-requests/', // Enterprise feature, expected in OSS
    '/release-pipelines/', // Enterprise feature, expected in OSS
    '/roles/', // May not exist in certain configurations
    '/saml/configuration/', // Enterprise feature, expected in OSS
  ],
  400: [
  ],
  403: [
    '/get-subscription-metadata/', // Expected for non-admin users
    '/usage-data/', // Expected for non-admin users
    '/invite-links/', // Expected for non-admin users
    '/roles/', // Expected for non-admin users
    '/change-requests/', // Expected for non-admin users
    '/api-keys/', // Expected for non-admin users
    '/metrics/', // Expected for non-admin users
    '/invites/', // Expected for non-admin users
  ],
  429: [
    '/usage-data/', // Usage data endpoint has rate limiting, throttling is expected
  ],
};

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
    const ignoreUrls = IGNORE_RESPONSE_ERRORS[status];
    if (ignoreUrls && ignoreUrls.some(pattern => url.includes(pattern))) {
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

  async waitForElementVisible(selector: string, timeout: number = LONG_TIMEOUT) {
    logUsingLastSection(`Waiting element visible ${selector}`);
    await this.page.locator(selector).first().waitFor({
      state: 'visible',
      timeout
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

  async navigateToSegment(name: string) {
    const segmentList = this.page.locator('#segment-list');
    const segmentElement = segmentList.locator('[data-test^="segment-"][data-test$="-name"]').filter({ hasText: name }).first();
    await segmentElement.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await segmentElement.scrollIntoViewIfNeeded();
    await segmentElement.click();
  }

  async waitForElementNotExist(selector: string) {
    logUsingLastSection(`Waiting element not exist ${selector}`);
    await expect(this.page.locator(selector)).toHaveCount(0, { timeout: 10000 });
  }

  async waitForNetworkIdle() {
    await this.page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {
      // Silently continue if timeout - page might already be idle
    });
  }

  async waitForDomContentLoaded() {
    await this.page.waitForLoadState('domcontentloaded', { timeout: 10000 }).catch(() => {
      // Silently continue if timeout - DOM might already be loaded
    });
  }

  async waitForPageFullyLoaded() {
    await this.waitForDomContentLoaded();
    await this.waitForNetworkIdle();
  }

  async getInputValue(selector: string): Promise<string> {
    const element = this.page.locator(selector).first();
    await element.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    return await element.inputValue();
  }

  async scrollBy(x: number, y: number) {
    await this.page.evaluate(({ x, y }) => {
      window.scrollBy(x, y);
    }, { x, y });
  }

  async gotoFeatures() {
    await this.click('#features-link');
    await this.waitForElementVisible('#show-create-feature-btn');
    await this.waitForPageFullyLoaded();
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

  async login(
    email: string = process.env.E2E_USER || '',
    password: string = process.env.E2E_PASS || '',
  ) {
    await this.page.goto('/login');
    // Wait for both fields to be visible
    await this.waitForElementVisible('[name="email"]');
    await this.waitForElementVisible('[name="password"]');
    // Small delay to let any autofocus logic complete
    await this.page.waitForTimeout(500);
    // Now fill the fields - fill() handles focus internally
    await this.setText('[name="email"]', email);
    await this.setText('[name="password"]', password);
    await this.click('#login-btn');
    // Wait for navigation to complete - either to an organization or create page
    await this.page.waitForURL((url) => {
      return url.pathname.includes('/organisation/') || url.pathname.includes('/create');
    }, { timeout: LONG_TIMEOUT });

    // Check if we're on the create page (no organizations)
    const currentUrl = this.page.url();
    if (currentUrl.includes('/create')) {
      // User has no organizations, we're on the create page
      log('User has no organizations, on create page');
    } else {
      // Wait for the project manage widget to be present and projects to load
      await this.waitForElementVisible('#project-manage-widget');
    }
    // Wait for loading to complete - either project list or no projects message appears
    await this.page.waitForFunction(() => {
      const widget = document.querySelector('#project-manage-widget');
      if (!widget) return true; // If no widget, we're on create page - that's ok
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

  async assertTextContent(selector: string, expectedText: string) {
    await expect(this.page.locator(selector)).toContainText(expectedText);
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

  // Navigate to traits page for a specific user
  async gotoTraits(identifier: string) {
    await this.click('#features-link');
    await this.click('#users-link');
    const userRow = this.page.locator('[data-test^="user-item-"]').filter({ hasText: identifier }).first();
    await userRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await userRow.click();
    await this.waitForElementVisible('#add-trait');
  }

  // Navigate to a user
  async goToUser(identifier: string) {
    await this.click('#features-link');
    await this.click('#users-link');
    const userRow = this.page.locator('[data-test^="user-item-"]').filter({ hasText: identifier }).first();
    await userRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await userRow.click();
  }

  // Navigate to a feature
  async gotoFeature(name: string) {
    const featureRow = this.page.locator('[data-test^="feature-item-"]').filter({
      has: this.page.locator(`text="${name}"`)
    }).first();
    await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await featureRow.click();
    await this.waitForElementVisible('#create-feature-modal');
  }

  // Create a feature
  async createFeature({ name, value, description = 'description' }: { name: string, value?: string | boolean | number, description?: string }) {
    await this.gotoFeatures();
    await this.click('#show-create-feature-btn');
    await this.setText(byId('featureID'), name);
    await this.setText(byId('featureDesc'), description);
    if (value) {
      await this.click(byId('toggle-feature-button'));
    }
    await this.page.waitForTimeout(500);
    await this.click(byId('create-feature-btn'));
    await this.page.waitForTimeout(1500);
    const featureElement = this.page.locator('[data-test^="feature-item-"]').filter({
      has: this.page.locator(`span:text-is("${name}")`)
    }).first();
    await featureElement.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await this.closeModal();
    await this.page.waitForTimeout(500);
  }

  // Create a remote config
  async createRemoteConfig({ name, value, description = 'description', defaultOff, mvs = [] }: { name: string, value: string | number | boolean, description?: string, defaultOff?: boolean, mvs?: MultiVariate[] }) {
    const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
    await this.gotoFeatures();
    await this.click('#show-create-feature-btn');
    await this.setText(byId('featureID'), name);
    await this.setText(byId('featureValue'), `${value}`);
    await this.setText(byId('featureDesc'), description);
    if (!defaultOff) {
      await this.click(byId('toggle-feature-button'));
    }
    for (let i = 0; i < mvs.length; i++) {
      const v = mvs[i];
      await this.click(byId('add-variation'));
      await this.page.waitForTimeout(200);
      await this.setText(byId(`featureVariationValue${i}`), v.value);
      await this.setText(byId(`featureVariationWeight${v.value}`), `${v.weight}`);
      await this.page.waitForTimeout(100);
    }
    await this.page.waitForTimeout(500);
    await this.click(byId('create-feature-btn'));
    await this.page.waitForTimeout(2000);
    const timeout = mvs.length > 0 ? 45000 : 20000;
    const featureElement = this.page.locator('[data-test^="feature-item-"]').filter({
      has: this.page.locator(`span:text-is("${name}")`)
    }).first();
    await featureElement.waitFor({ state: 'visible', timeout });
    const valueElement = featureElement.locator('[data-test^="feature-value-"]');
    await expect(valueElement).toHaveText(expectedValue, { timeout });
    await this.closeModal();
    await this.page.waitForTimeout(500);
  }

  // Delete a feature
  async deleteFeature(name: string) {
    const featureRow = this.page.locator('[data-test^="feature-item-"]').filter({
      has: this.page.locator(`span:text-is("${name}")`)
    }).first();
    await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    const dataTest = await featureRow.getAttribute('data-test');
    const index = dataTest?.match(/feature-item-(\d+)/)?.[1];
    if (!index) {
      throw new Error(`Could not find index for feature: ${name}`);
    }
    await this.click(byId(`feature-action-${index}`));
    await this.waitForElementVisible(byId(`feature-remove-${index}`));
    await this.click(byId(`feature-remove-${index}`));
    await this.setText('[name="confirm-feature-name"]', name);
    await this.click('#confirm-remove-feature-btn');
    await expect(this.page.locator('[data-test^="feature-item-"]').filter({
      has: this.page.locator(`span:text-is("${name}")`)
    })).toHaveCount(0, { timeout: LONG_TIMEOUT });
  }

  // Toggle a feature
  async toggleFeature(name: string, value: boolean) {
    const featureRow = this.page.locator('[data-test^="feature-item-"]').filter({
      has: this.page.locator(`span:text-is("${name}")`)
    }).first();
    await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    const currentState = value ? 'off' : 'on';
    const switchElement = featureRow.locator(`[data-test^="feature-switch-"][data-test$="-${currentState}"]`).first();
    await switchElement.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await switchElement.click();
    await this.click('#confirm-toggle-feature-btn');
    const newState = value ? 'on' : 'off';
    const newSwitchElement = featureRow.locator(`[data-test^="feature-switch-"][data-test$="-${newState}"]`).first();
    await newSwitchElement.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
  }

  // Create a trait
  async createTrait(name: string, value: string | boolean | number) {
    await this.click('#add-trait');
    await this.waitForElementVisible('#create-trait-modal');
    await this.setText('[name="traitID"]', name);
    await this.setText('[name="traitValue"]', `${value}`);
    await this.click('#create-trait-btn');
    await this.page.waitForTimeout(2000);
    await this.page.reload();
    const traitNameElement = this.page.locator('[class*="js-trait-key-"]').filter({ hasText: new RegExp(`^${name}$`) });
    await traitNameElement.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    const className = await traitNameElement.getAttribute('class');
    const index = className?.match(/js-trait-key-(\d+)/)?.[1];
    const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
    await expect(this.page.locator(byId(`user-trait-value-${index}`))).toContainText(expectedValue);
  }

  // Delete a trait
  async deleteTrait(name: string) {
    const traitElement = this.page.locator('[class*="js-trait-key-"]').filter({ hasText: new RegExp(`^${name}$`) });
    await traitElement.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    const className = await traitElement.getAttribute('class');
    const index = className?.match(/js-trait-key-(\d+)/)?.[1];
    await this.click(byId(`delete-user-trait-${index}`));
    await this.click('#confirm-btn-yes');
    await this.page.waitForFunction((traitName) => {
      const traitElements = document.querySelectorAll('[class*="js-trait-key-"]');
      for (const element of traitElements as any) {
        if (element.textContent?.trim() === traitName) {
          return false;
        }
      }
      return true;
    }, name, { timeout: LONG_TIMEOUT });
  }

  // Clone a segment
  async cloneSegment(name: string, clonedName: string) {
    const segmentRow = this.page.locator('.list-item').filter({ hasText: name }).first();
    const actionButton = segmentRow.locator('[data-test^="segment-action-"]');
    await actionButton.click();
    const cloneButton = segmentRow.locator('[data-test^="segment-clone-"]');
    await cloneButton.click();
    await this.setText('[name="clone-segment-name"]', clonedName);
    await this.click('#confirm-clone-segment-btn');
    await this.page.locator('.list-item').filter({ hasText: clonedName }).first().waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
  }

  // Delete a segment
  async deleteSegment(name: string) {
    const segmentRow = this.page.locator('.list-item').filter({ hasText: name }).first();
    const actionButton = segmentRow.locator('[data-test^="segment-action-"]');
    await actionButton.click();
    const removeButton = segmentRow.locator('[data-test^="segment-remove-"]');
    await removeButton.click();
    await this.setText('[name="confirm-segment-name"]', name);
    await this.click('#confirm-remove-segment-btn');
    await expect(this.page.locator('.list-item').filter({ hasText: name })).toHaveCount(0, { timeout: LONG_TIMEOUT });
  }

  // Close modal
  async closeModal() {
    log('Close Modal');
    await this.page.mouse.click(50, 50);
    // Wait for modal to fully close by checking body no longer has modal-open class
    await this.page.waitForFunction(
      () => !document.body.classList.contains('modal-open'),
      { timeout: LONG_TIMEOUT }
    );
  }

  // Save feature segments
  async saveFeatureSegments() {
    await this.click('#update-feature-segments-btn');
    await this.waitForElementVisible('.toast-message', 10000);
    await this.page.locator('.toast-message').waitFor({ state: 'hidden', timeout: 10000 });
    await this.closeModal();
    await this.waitForElementNotExist('#create-feature-modal');
  }

  // Wait and refresh
  async waitAndRefresh(waitFor: number = 3000) {
    await this.page.waitForTimeout(waitFor);
    await this.page.reload();
    await this.waitForPageFullyLoaded();
  }

  // Create a role
  async createRole(name: string, users: number[]) {
    await this.click(byId('tab-item-roles'));
    await this.click(byId('create-role'));
    await this.setText(byId('role-name'), name);
    await this.click(byId('save-role'));
    await this.closeModal();
    // Click on the role by its name
    const roleRow = this.page.locator('[data-test^="role-"]').filter({ hasText: name }).first();
    await roleRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await roleRow.click();
    await this.click(byId('members-tab'));
    await this.click(byId('assigned-users'));
    for (const userId of users) {
      await this.click(byId(`assignees-list-item-${userId}`));
    }
    await this.closeModal();
  }

  // Assert user feature value
  async assertUserFeatureValue(name: string, expectedValue: string) {
    const featureRow = this.page.locator('[data-test^="user-feature-"]').filter({
      has: this.page.locator(`text="${name}"`)
    }).first();
    await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    const valueElement = featureRow.locator('[data-test^="user-feature-value-"]');
    await expect(valueElement).toHaveText(expectedValue, { timeout: LONG_TIMEOUT });
  }

  // Wait for user feature switch state
  async waitForUserFeatureSwitch(name: string, state: 'on' | 'off') {
    const featureRow = this.page.locator('[data-test^="user-feature-"]').filter({
      has: this.page.locator(`text="${name}"`)
    }).first();
    await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    const switchElement = featureRow.locator(`[data-test^="user-feature-switch-"][data-test$="-${state}"]`);
    await switchElement.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
  }

  // Click user feature switch
  async clickUserFeatureSwitch(name: string, state: 'on' | 'off') {
    const featureRow = this.page.locator('[data-test^="user-feature-"]').filter({
      has: this.page.locator(`text="${name}"`)
    }).first();
    await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    const switchElement = featureRow.locator(`[data-test^="user-feature-switch-"][data-test$="-${state}"]`).first();
    await switchElement.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await switchElement.click();
  }

  // Click user feature (to open edit modal)
  async clickUserFeature(name: string) {
    const featureRow = this.page.locator('[data-test^="user-feature-"]').filter({
      has: this.page.locator(`text="${name}"`)
    }).first();
    await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await featureRow.click();
  }

  // Assert input value
  async assertInputValue(selector: string, value: string) {
    await expect(this.page.locator(selector)).toHaveValue(value);
  }

  // Wait for feature switch state (in features list)
  async waitForFeatureSwitch(name: string, state: 'on' | 'off') {
    const featureRow = this.page.locator('[data-test^="feature-item-"]').filter({
      has: this.page.locator(`span:text-is("${name}")`)
    }).first();
    await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    const switchElement = featureRow.locator(`[data-test^="feature-switch-"][data-test$="-${state}"]`);
    await switchElement.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
  }

  // Delete segment from the segment detail page
  async deleteSegmentFromPage(name: string) {
    await this.click(byId('remove-segment-btn'));
    await this.setText('[name="confirm-segment-name"]', name);
    await this.click('#confirm-remove-segment-btn');
    await this.waitForElementVisible(byId('show-create-segment-btn'));
  }

  // Set segment rule
  async setSegmentRule(ruleIndex: number, orIndex: number, name: string, operator: string, value: string | number | boolean) {
    await this.setText(byId(`rule-${ruleIndex}-property-${orIndex}`), name);
    if (operator) {
      await this.setText(byId(`rule-${ruleIndex}-operator-${orIndex}`), operator);
      await this.page.waitForTimeout(200);
    }
    await this.waitForElementVisible(byId(`rule-${ruleIndex}-value-${orIndex}`));
    await this.setText(byId(`rule-${ruleIndex}-value-${orIndex}`), `${value}`);
  }

  // Create a segment
  async createSegment(name: string, rules?: Rule[]) {
    await this.click(byId('show-create-segment-btn'));
    await this.setText(byId('segmentID'), name);
    if (rules && rules.length > 0) {
      for (let x = 0; x < rules.length; x++) {
        const rule = rules[x];
        if (x > 0) {
          await this.click(byId('add-rule'));
          await this.waitForElementVisible(byId(`rule-${x}-property-0`));
        }
        await this.setSegmentRule(x, 0, rule.name, rule.operator, rule.value);
        if (rule.ors) {
          for (let orIndex = 0; orIndex < rule.ors.length; orIndex++) {
            const or = rule.ors[orIndex];
            await this.click(byId(`rule-${x}-or`));
            await this.waitForElementVisible(byId(`rule-${x}-property-${orIndex + 1}`));
            await this.setSegmentRule(x, orIndex + 1, or.name, or.operator, or.value);
          }
        }
      }
    }
    await this.click(byId('create-segment'));
    const element = this.page.locator('[data-test^="segment-"][data-test$="-name"]').filter({ hasText: name });
    await element.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
  }

  // Open segment override dropdown and select a segment
  private async openSegmentOverride(index: number, selectionIndex: number = 0) {
    const dropdownSelector = byId(`select-segment-option-${selectionIndex}`);
    const isDropdownVisible = await this.page.locator(dropdownSelector).isVisible().catch(() => false);
    if (!isDropdownVisible) {
      await this.click(byId('segment_overrides'));
    }
    await this.click(dropdownSelector);
    await this.waitForElementVisible(byId(`segment-override-value-${index}`));
  }

  // Add segment override for boolean flags
  async addSegmentOverride(index: number, value: boolean, selectionIndex: number = 0, mvs: MultiVariate[] = []) {
    await this.openSegmentOverride(index, selectionIndex);
    if (mvs && mvs.length > 0) {
      for (const v of mvs) {
        const weightSelector = `.segment-overrides ${byId(`featureVariationWeight${v.value}`)}`;
        await this.waitForElementVisible(weightSelector);
        await this.setText(weightSelector, `${v.weight}`);
        await this.page.waitForTimeout(100);
      }
      await this.page.waitForTimeout(500);
    }
    if (value) {
      await this.click(byId(`segment-override-toggle-${index}`));
    }
  }

  // Add segment override for remote configs
  async addSegmentOverrideConfig(index: number, value: string | number | boolean, selectionIndex: number = 0) {
    await this.openSegmentOverride(index, selectionIndex);
    await this.setText(byId(`segment-override-value-${index}`), `${value}`);
    await this.click(byId(`segment-override-toggle-${index}`));
  }

  // Set segment override index (for reordering)
  async setSegmentOverrideIndex(index: number, newIndex: number) {
    await this.click(byId('segment_overrides'));
    await this.setText(byId(`sort-${index}`), `${newIndex}`);
  }

  // Edit remote config
  async editRemoteConfig(featureName: string, value: string | number | boolean, toggleFeature: boolean = false, mvs: MultiVariate[] = []) {
    await this.gotoFeatures();
    const featureRow = this.page.locator('[data-test^="feature-item-"]').filter({
      has: this.page.locator(`text="${featureName}"`)
    }).first();
    await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await featureRow.click();
    if (value !== '') {
      await this.setText(byId('featureValue'), `${value}`);
    }
    if (mvs.length > 0) {
      await this.page.waitForTimeout(500);
      for (const v of mvs) {
        const selector = byId(`featureVariationWeight${v.value}`);
        await this.waitForElementVisible(selector);
        const input = this.page.locator(selector);
        await input.clear();
        await this.page.waitForTimeout(100);
        await input.fill(`${v.weight}`);
        await this.page.waitForTimeout(100);
        await input.blur();
        await this.page.waitForTimeout(500);
      }
    }
    if (toggleFeature) {
      await this.click(byId('toggle-feature-button'));
    }
    if (mvs.length > 0 || value !== '') {
      await this.page.waitForTimeout(1500);
    }
    await this.click(byId('update-feature-btn'));
    await this.waitForElementVisible('.toast-message', 10000);
    await this.page.locator('.toast-message').waitFor({ state: 'hidden', timeout: 10000 });
    await this.closeModal();
    await this.waitForElementNotExist('#create-feature-modal');
  }

  // Create an environment
  async createEnvironment(name: string) {
    await this.waitForElementVisible('[name="envName"]');
    const nameInput = this.page.locator('[name="envName"]').first();
    await nameInput.click();
    await nameInput.fill(name);
    await this.click('#create-env-btn');
    await this.waitForElementVisible(byId(`switch-environment-${name.toLowerCase()}-active`));
  }

  // Create organisation and project
  async createOrganisationAndProject(organisationName: string, projectName: string) {
    log('Create Organisation');
    await this.click(byId('home-link'));
    await this.click(byId('create-organisation-btn'));
    await this.setText('[name="orgName"]', organisationName);
    await this.click('#create-org-btn');
    await this.page.waitForURL(/\/organisation\/\d+/, { timeout: LONG_TIMEOUT });
    await this.waitForElementVisible(byId('project-manage-widget'));
    await this.page.waitForFunction(() => {
      const widget = document.querySelector('#project-manage-widget');
      if (!widget) return false;
      const hasLoader = widget.querySelector('.centered-container .loader');
      return !hasLoader;
    }, { timeout: LONG_TIMEOUT });

    log('Create Project');
    await this.click('.btn-project-create');
    await this.setText(byId('projectName'), projectName);
    await this.click(byId('create-project-btn'));
    await this.waitForElementVisible(byId('features-page'));
  }

  // Get text content of an element
  async getText(selector: string): Promise<string> {
    return await this.page.locator(selector).innerText();
  }

  // Parse try it results
  async parseTryItResults(): Promise<Record<string, any>> {
    const text = await this.getText('#try-it-results');
    try {
      return JSON.parse(text);
    } catch (e) {
      throw new Error('Try it results are not valid JSON');
    }
  }

  // Go to feature versions
  async goToFeatureVersions(featureName: string) {
    await this.gotoFeature(featureName);
    if (await this.isElementExists('change-history')) {
      await this.click(byId('change-history'));
    } else {
      await this.click(byId('tabs-overflow-button'));
      await this.click(byId('change-history'));
    }
  }

  // Compare version
  async compareVersion(
    featureName: string,
    versionIndex: number,
    compareOption: 'LIVE' | 'PREVIOUS' | null,
    oldEnabled: boolean,
    newEnabled: boolean,
    oldValue?: any,
    newValue?: any,
  ) {
    await this.goToFeatureVersions(featureName);
    await this.click(byId(`history-item-${versionIndex}-compare`));
    if (compareOption === 'LIVE') {
      await this.click(byId(`history-item-${versionIndex}-compare-live`));
    } else if (compareOption === 'PREVIOUS') {
      await this.click(byId(`history-item-${versionIndex}-compare-previous`));
    }

    // Wait for comparison modal to fully load data
    await this.page.waitForTimeout(2000);

    // Use .first() to handle cases where multiple comparison modals might exist in DOM
    await expect(this.page.locator(byId('old-enabled')).first()).toHaveText(`${oldEnabled}`);
    await expect(this.page.locator(byId('new-enabled')).first()).toHaveText(`${newEnabled}`);
    if (oldValue !== undefined) {
      const expectedOldValue = oldValue === null ? '' : `${oldValue}`;
      await expect(this.page.locator(byId('old-value')).first()).toHaveText(expectedOldValue);
    }
    if (newValue !== undefined) {
      const expectedNewValue = newValue === null ? '' : `${newValue}`;
      await expect(this.page.locator(byId('new-value')).first()).toHaveText(expectedNewValue);
    }
    await this.closeModal();
  }

  // Assert number of versions
  async assertNumberOfVersions(featureName: string, versions: number) {
    await this.goToFeatureVersions(featureName);
    await this.waitForElementVisible(byId(`history-item-${versions - 2}-compare`));
    await this.closeModal();
  }

  // Get feature index by name
  async getFeatureIndexByName(featureName: string): Promise<number> {
    const featureRow = this.page.locator('[data-test^="feature-item-"]').filter({
      has: this.page.locator(`span:text-is("${featureName}")`)
    }).first();

    await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });

    const dataTest = await featureRow.getAttribute('data-test');
    const index = dataTest?.match(/feature-item-(\d+)/)?.[1];

    if (!index) {
      throw new Error(`Could not find index for feature: ${featureName}`);
    }

    return parseInt(index, 10);
  }

  // Click feature action button
  async clickFeatureAction(featureName: string) {
    const index = await this.getFeatureIndexByName(featureName);
    await this.click(byId(`feature-action-${index}`));
  }

  // Wait for feature switch by name and state to be clickable or not clickable
  async waitForFeatureSwitchClickable(featureName: string, state: 'on' | 'off', clickable: boolean = true) {
    const featureRow = this.page.locator('[data-test^="feature-item-"]').filter({
      has: this.page.locator(`span:text-is("${featureName}")`)
    }).first();

    await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });

    const element = featureRow.locator(`[data-test^="feature-switch-"][data-test$="-${state}"]`).first();
    await element.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    if (clickable) {
      await expect(element).toBeEnabled({ timeout: LONG_TIMEOUT });
    } else {
      await expect(element).toBeDisabled({ timeout: LONG_TIMEOUT });
    }
  }

  // Set user permission
  async setUserPermission(
    email: string,
    permission: string,
    entityName: string | null,
    entityLevel?: 'project' | 'environment' | 'organisation',
    parentName?: string,
  ) {
    const permissionsMap: Record<string, string> = {
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
    };
    await this.click(byId('users-and-permissions'));
    await this.click(byId(`user-${email}`));
    const level = permissionsMap[permission] || entityLevel;
    await this.click(byId(`${level}-permissions-tab`));
    if (parentName) {
      await this.clickByText(parentName, 'a');
    }
    if (entityName) {
      await this.click(byId(`permissions-${entityName.toLowerCase()}`));
    }
    if (permission === 'ADMIN') {
      await this.click(byId(`admin-switch-${level}`));
    } else {
      await this.click(byId(`permission-switch-${permission}`));
    }
    await this.closeModal();
  }
}

// Export a factory function to create helpers for a page
// Returns an object with all methods bound to the instance so destructuring works
export function createHelpers(page: Page): E2EHelpers {
  const instance = new E2EHelpers(page);
  // Auto-bind all methods so destructuring works
  const proto = Object.getPrototypeOf(instance);
  const methodNames = Object.getOwnPropertyNames(proto).filter(
    name => name !== 'constructor' && typeof (instance as any)[name] === 'function'
  );
  const helpers: Record<string, any> = {};
  for (const name of methodNames) {
    helpers[name] = (instance as any)[name].bind(instance);
  }
  return helpers as E2EHelpers;
}

