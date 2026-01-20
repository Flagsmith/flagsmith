import { Page, expect, Locator } from '@playwright/test';
import Project from '../common/project';
import fetch from 'node-fetch';
import flagsmith from 'flagsmith/isomorphic';
import { IFlagsmith } from 'flagsmith/types';

export const LONG_TIMEOUT = 40000;

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
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await element.clear();
    if (text) {
      await element.fill(text);
    }
  }

  async waitForElementVisible(selector: string) {
    logUsingLastSection(`Waiting element visible ${selector}`);
    await this.page.locator(selector).waitFor({
      state: 'visible',
      timeout: LONG_TIMEOUT
    });
  }

  async waitForElementNotClickable(selector: string) {
    logUsingLastSection(`Waiting element not clickable ${selector}`);
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
    await expect(element).toBeDisabled();
  }

  async waitForElementClickable(selector: string) {
    logUsingLastSection(`Waiting element clickable ${selector}`);
    const element = this.page.locator(selector);
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
    const element = this.page.locator(selector);
    await element.scrollIntoViewIfNeeded();
    await expect(element).toBeEnabled({ timeout: 5000 });
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
    await this.setText(byId('email'), email);
    await this.setText(byId('password'), password);
    await this.click(byId('btn-login'));
    await this.waitForElementVisible('#project-select-page');
  }

  async logout() {
    try {
      await this.page.locator('#org-menu').click();
      await this.clickByText('Logout');
      await this.waitForElementVisible('#btn-login');
    } catch (e) {
      console.log('Could not log out:', e);
    }
  }

  // Additional helper methods for common operations
  async selectToggle(selector: string, value: boolean = true) {
    const element = this.page.locator(selector);
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