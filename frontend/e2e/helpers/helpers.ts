import { Page, expect } from '@playwright/test';
import { FlagsmithValue } from '../../common/types/responses';

export const LONG_TIMEOUT = 40000;

export const byId = (id: string) => `[data-test="${id}"]`;

export type MultiVariate = { value: string; weight: number };

export type Rule = {
  name: string;
  operator: string;
  value: string | number | boolean;
  ors?: Rule[];
};

export const setText = async (page: Page, selector: string, text: string) => {
  logUsingLastSection(`Set text ${selector} : ${text}`);
  if (text) {
    await page.fill(selector, text);
  } else {
    await page.fill(selector, '');
  }
};

export const waitForElementVisible = async (page: Page, selector: string) => {
  logUsingLastSection(`Waiting element visible ${selector}`);
  await expect(page.locator(selector)).toBeVisible({ timeout: LONG_TIMEOUT });
};

export const waitForElementNotClickable = async (page: Page, selector: string) => {
  logUsingLastSection(`Waiting element visible ${selector}`);
  await expect(page.locator(selector)).toBeVisible({ timeout: LONG_TIMEOUT });
  await expect(page.locator(selector)).toHaveAttribute('disabled', '');
};

export const waitForElementClickable = async (page: Page, selector: string) => {
  logUsingLastSection(`Waiting element visible ${selector}`);
  await expect(page.locator(selector)).toBeVisible({ timeout: LONG_TIMEOUT });
  await expect(page.locator(selector)).not.toHaveAttribute('disabled', '');
};

export const waitForElementNotExist = async (page: Page, selector: string) => {
  logUsingLastSection(`Waiting element not visible ${selector}`);
  await expect(page.locator(selector)).not.toBeVisible({ timeout: 10000 });
};

export const gotoFeatures = async (page: Page) => {
  await click(page, '#features-link');
  await waitForElementVisible(page, '#show-create-feature-btn');
};

export const click = async (page: Page, selector: string) => {
  await waitForElementVisible(page, selector);
  const element = page.locator(selector);
  await element.scrollIntoViewIfNeeded();
  await expect(element).not.toHaveAttribute('disabled', '');
  await element.hover();
  await element.click();
};

export const clickByText = async (page: Page, text: string, element = 'button') => {
  logUsingLastSection(`Click by text ${text} ${element}`);
  const selector = page.locator(element).filter({ hasText: text });
  await selector.scrollIntoViewIfNeeded();
  await expect(selector).not.toHaveAttribute('disabled', '');
  await selector.hover();
  await selector.click();
};

export const gotoSegments = async (page: Page) => {
  await click(page, '#segments-link');
};

export const createRole = async (page: Page, roleName: string, index: number, users: number[]) => {
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

export const editRoleMembers = async (page: Page, index: number, roleName: string) => {
  await click(page, byId('tab-item-roles'));
  await click(page, byId('create-role'));
  await setText(page, byId('role-name'), roleName);
  await click(page, byId('save-role'));
};

export const gotoTraits = async (page: Page) => {
  await click(page, '#features-link');
  await click(page, '#users-link');
  await click(page, byId('user-item-0'));
  await waitForElementVisible(page, '#add-trait');
};

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

export const deleteTrait = async (page: Page, index: number) => {
  await click(page, byId(`delete-user-trait-${index}`));
  await click(page, '#confirm-btn-yes');
  await waitForElementNotExist(page, byId(`user-trait-${index}`));
};

const lastTestSection: Record<string, string> = {};
let lastTestName: string | undefined;

export const logUsingLastSection = (message?: string) => {
  log(undefined, message);
};

export const log = (section: string | undefined, message?: string) => {
  const testName = process.env.TEST_NAME;
  const sectionName = section ?? lastTestSection[testName || ''];

  if (lastTestName !== testName || lastTestSection[testName || ''] !== sectionName) {
    const ellipsis = section === sectionName ? '' : '...';
    console.log(
      '\n',
      '\x1b[32m',
      `${testName ? `${ellipsis}[${testName} tests] ` : ''}${sectionName}`,
      '\x1b[0m',
      '\n',
    );
    if (testName) {
      lastTestSection[testName] = sectionName;
    }
    lastTestName = testName;
  }
  if (message) {
    console.log(message);
  }
};

export const viewFeature = async (page: Page, index: number) => {
  await click(page, byId(`feature-item-${index}`));
  await waitForElementVisible(page, '#create-feature-modal');
};

export const addSegmentOverrideConfig = async (
  page: Page,
  index: number,
  value: string | boolean | number,
  selectionIndex = 0,
) => {
  await click(page, byId('segment_overrides'));
  await click(page, byId(`select-segment-option-${selectionIndex}`));
  await waitForElementVisible(page, byId(`segment-override-value-${index}`));
  await setText(page, byId(`segment-override-value-${index}`), `${value}`);
  await click(page, byId(`segment-override-toggle-${index}`));
};

export const addSegmentOverride = async (
  page: Page,
  index: number,
  value: string | boolean | number,
  selectionIndex = 0,
  mvs: MultiVariate[] = [],
) => {
  await click(page, byId('segment_overrides'));
  await click(page, byId(`select-segment-option-${selectionIndex}`));
  await waitForElementVisible(page, byId(`segment-override-value-${index}`));
  if (value) {
    await click(page, `${byId(`segment-override-${index}`)} [role="switch"]`);
  }
  if (mvs) {
    await Promise.all(
      mvs.map(async (v) => {
        await setText(
          page,
          `.segment-overrides ${byId(`featureVariationWeight${v.value}`)}`,
          `${v.weight}`,
        );
      }),
    );
  }
};

export const saveFeature = async (page: Page) => {
  await click(page, '#update-feature-btn');
  await waitForElementVisible(page, '.toast-message');
  await waitForElementNotExist(page, '.toast-message');
  await closeModal(page);
  await waitForElementNotExist(page, '#create-feature-modal');
};

export const saveFeatureSegments = async (page: Page) => {
  await click(page, '#update-feature-segments-btn');
  await waitForElementVisible(page, '.toast-message');
  await waitForElementNotExist(page, '.toast-message');
  await closeModal(page);
  await waitForElementNotExist(page, '#create-feature-modal');
};

export const createEnvironment = async (page: Page, name: string) => {
  await setText(page, '[name="envName"]', name);
  await click(page, '#create-env-btn');
  await waitForElementVisible(page, byId(`switch-environment-${name.toLowerCase()}-active`));
};

export const goToUser = async (page: Page, index: number) => {
  await click(page, '#features-link');
  await click(page, '#users-link');
  await click(page, byId(`user-item-${index}`));
};

export const gotoFeature = async (page: Page, index: number) => {
  await click(page, byId(`feature-item-${index}`));
  await waitForElementVisible(page, '#create-feature-modal');
};

export const setSegmentOverrideIndex = async (
  page: Page,
  index: number,
  newIndex: number,
) => {
  await click(page, byId('segment_overrides'));
  await setText(page, byId(`sort-${index}`), `${newIndex}`);
};

export const assertTextContent = async (page: Page, selector: string, v: string) =>
  await expect(page.locator(selector)).toHaveText(v);

export const assertTextContentContains = async (page: Page, selector: string, v: string) =>
  await expect(page.locator(selector)).toContainText(v);

export const getText = async (page: Page, selector: string) =>
  await page.locator(selector).innerText();

export const deleteSegment = async (page: Page, index: number, name: string) => {
  await click(page, byId(`remove-segment-btn-${index}`));
  await setText(page, '[name="confirm-segment-name"]', name);
  await click(page, '#confirm-remove-segment-btn');
  await waitForElementNotExist(page, `remove-segment-btn-${index}`);
};

export const login = async (page: Page, email: string, password: string) => {
  await page.goto('');
  // await page.addScriptTag({ path: '../../api/index.js' });
  await setText(page, '[name="email"]', `${email}`);
  await setText(page, '[name="password"]', `${password}`);
  await click(page, '#login-btn');
  await waitForElementVisible(page, '#project-manage-widget');
};

export const logout = async (page: Page) => {
  await click(page, '#account-settings-link');
  await click(page, '#logout-link');
  await waitForElementVisible(page, '#login-page');
};

export const goToFeatureVersions = async (page: Page, featureIndex: number) => {
  await gotoFeature(page, featureIndex);
  await click(page, byId('change-history'));
};

export const compareVersion = async (
  page: Page,
  featureIndex: number,
  versionIndex: number,
  compareOption: 'LIVE' | 'PREVIOUS' | null,
  oldEnabled: boolean,
  newEnabled: boolean,
  oldValue?: FlagsmithValue,
  newValue?: FlagsmithValue,
) => {
  await goToFeatureVersions(page, featureIndex);
  await click(page, byId(`history-item-${versionIndex}-compare`));
  if (compareOption === 'LIVE') {
    await click(page, byId(`history-item-${versionIndex}-compare-live`));
  } else if (compareOption === 'PREVIOUS') {
    await click(page, byId(`history-item-${versionIndex}-compare-previous`));
  }

  await assertTextContent(page, byId(`old-enabled`), `${oldEnabled}`);
  await assertTextContent(page, byId(`new-enabled`), `${newEnabled}`);
  if (oldValue) {
    await assertTextContent(page, byId(`old-value`), `${oldValue}`);
  }
  if (newValue) {
    await assertTextContent(page, byId(`old-value`), `${oldValue}`);
  }
  await closeModal(page);
};

export const assertNumberOfVersions = async (page: Page, index: number, versions: number) => {
  await goToFeatureVersions(page, index);
  await waitForElementVisible(page, byId(`history-item-${versions - 2}-compare`));
  await closeModal(page);
};

export const createRemoteConfig = async (
  page: Page,
  index: number,
  name: string,
  value: string | number | boolean,
  description = 'description',
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
  await Promise.all(
    mvs.map(async (v, i) => {
      await click(page, byId('add-variation'));
      await setText(page, byId(`featureVariationValue${i}`), v.value);
      await setText(page, byId(`featureVariationWeight${v.value}`), `${v.weight}`);
    }),
  );
  await click(page, byId('create-feature-btn'));
  await waitForElementVisible(page, byId(`feature-value-${index}`));
  await assertTextContent(page, byId(`feature-value-${index}`), expectedValue);
  await closeModal(page);
};

export const createOrganisationAndProject = async (page: Page, organisationName: string, projectName: string) => {
  log('Create Organisation');
  await click(page, byId('home-link'));
  await click(page, byId('create-organisation-btn'));
  await setText(page, '[name="orgName"]', organisationName);
  await click(page, '#create-org-btn');
  await waitForElementVisible(page, byId('project-manage-widget'));

  log('Create Project');
  await click(page, '.btn-project-create');
  await setText(page, byId('projectName'), projectName);
  await click(page, byId('create-project-btn'));
  await waitForElementVisible(page, byId('features-page'));
};

export const editRemoteConfig = async (
  page: Page,
  index: number,
  value: string | number | boolean,
  toggleFeature = false,
  mvs: MultiVariate[] = [],
) => {
  const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
  await gotoFeatures(page);
  await click(page, byId(`feature-item-${index}`));
  await setText(page, byId('featureValue'), `${value}`);
  if (toggleFeature) {
    await click(page, byId('toggle-feature-button'));
  }
  await Promise.all(
    mvs.map(async (v) => {
      await setText(page, byId(`featureVariationWeight${v.value}`), `${v.weight}`);
    }),
  );
  await click(page, byId('update-feature-btn'));
  if (value) {
    await waitForElementVisible(page, byId(`feature-value-${index}`));
    await assertTextContent(page, byId(`feature-value-${index}`), expectedValue);
  }
  await closeModal(page);
};

export const closeModal = async (page: Page) => {
  await page.click('body', {
    position: { x: 50, y: 50 },
  });
};

export const createFeature = async (
  page: Page,
  index: number,
  name: string,
  value?: string | boolean | number,
  description = 'description',
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

export const deleteFeature = async (page: Page, index: number, name: string) => {
  await click(page, byId(`feature-action-${index}`));
  await waitForElementVisible(page, byId(`remove-feature-btn-${index}`));
  await click(page, byId(`remove-feature-btn-${index}`));
  await setText(page, '[name="confirm-feature-name"]', name);
  await click(page, '#confirm-remove-feature-btn');
  await waitForElementNotExist(page, `remove-feature-btn-${index}`);
};

export const toggleFeature = async (page: Page, index: number, toValue: boolean) => {
  await click(page, byId(`feature-switch-${index}${toValue ? '-off' : 'on'}`));
  await click(page, '#confirm-toggle-feature-btn');
  await waitForElementVisible(page, byId(`feature-switch-${index}${toValue ? '-on' : 'off'}`));
};

export const setUserPermissions = async (page: Page, index: number, toValue: boolean) => {
  await click(page, byId(`feature-switch-${index}${toValue ? '-off' : 'on'}`));
  await click(page, '#confirm-toggle-feature-btn');
  await waitForElementVisible(page, byId(`feature-switch-${index}${toValue ? '-on' : 'off'}`));
};

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

export const createSegment = async (
  page: Page,
  index: number,
  id: string,
  rules?: Rule[],
) => {
  await click(page, byId('show-create-segment-btn'));
  await setText(page, byId('segmentID'), id);
  if (rules) {
    for (let x = 0; x < rules.length; x++) {
      const rule = rules[x];
      if (x > 0) {
        await click(page, byId('add-rule'));
      }
      await setSegmentRule(page, x, 0, rule.name, rule.operator, rule.value);
      if (rule.ors) {
        for (let orIndex = 0; orIndex < rule.ors.length; orIndex++) {
          const or = rule.ors[orIndex];
          await click(page, byId(`rule-${x}-or`));
          await setSegmentRule(page, x, orIndex + 1, or.name, or.operator, or.value);
        }
      }
    }
  }

  await click(page, byId('create-segment'));
  await waitForElementVisible(page, byId(`segment-${index}-name`));
  await assertTextContent(page, byId(`segment-${index}-name`), id);
  await closeModal(page);
};

export const waitAndRefresh = async (page: Page, waitFor = 3000) => {
  logUsingLastSection(`Waiting for ${waitFor}ms, then refreshing.`);
  await page.waitForTimeout(waitFor);
  await page.reload();
};

export const refreshUntilElementVisible = async (page: Page, selector: string, maxRetries = 20) => {
  const element = page.locator(selector);
  let retries = 0;
  while (retries < maxRetries && !(await element.isVisible())) {
    await page.reload();
    await page.waitForTimeout(3000);
    retries++;
  }
  await element.scrollIntoViewIfNeeded();
};

const permissionsMap = {
  'CREATE_PROJECT': 'organisation',
  'MANAGE_USERS': 'organisation',
  'MANAGE_USER_GROUPS': 'organisation',
  'VIEW_PROJECT': 'project',
  'CREATE_ENVIRONMENT': 'project',
  'DELETE_FEATURE': 'project',
  'CREATE_FEATURE': 'project',
  'MANAGE_SEGMENTS': 'project',
  'VIEW_AUDIT_LOG': 'project',
  'VIEW_ENVIRONMENT': 'environment',
  'UPDATE_FEATURE_STATE': 'environment',
  'MANAGE_IDENTITIES': 'environment',
  'CREATE_CHANGE_REQUEST': 'environment',
  'APPROVE_CHANGE_REQUEST': 'environment',
  'VIEW_IDENTITIES': 'environment',
  'MANAGE_SEGMENT_OVERRIDES': 'environment',
  'MANAGE_TAGS': 'project',
} as const;

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

export default {};
