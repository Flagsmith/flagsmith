import { Selector, t } from 'testcafe';

export const byId = id => `[data-test="${id}"]`;

export const setText = async (selector, text) => {
    console.log(`Set text ${selector} : ${text}`);
    return t.selectText(selector)
        .pressKey('delete')
        .selectText(selector) // Prevents issue where input tabs out of focus
        .typeText(selector, text);
};

export const waitForElementVisible = async (selector) => {
    console.log(`Waiting element visible ${selector}`);
    return t.expect(Selector(selector).visible).ok();
};
export const waitForElementNotExist = async (selector) => {
    console.log(`Waiting element not visible ${selector}`);
    return t.expect(Selector(selector).exists).notOk('', { timeout: 10 });
};
export const gotoFeatures = async () => {
    await t.click('#features-link');
    await waitForElementVisible('#show-create-feature-btn');
};

export const assertTextContent = (selector, v) => t.expect(Selector(selector).textContent).eql(v);
export const getText = selector => Selector(selector).innerText;

export const createRemoteConfig = async (index, name, value, description = 'description') => {
    const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
    await gotoFeatures();
    await t.click('#show-create-feature-btn');
    await setText(byId('featureID'), name);
    await setText(byId('featureValue'), value);
    await setText(byId('featureDesc'), description);
    await t.click(byId('create-feature-btn'));
    await waitForElementVisible(byId(`feature-value-${index}`));
    await assertTextContent(byId(`feature-value-${index}`), expectedValue);
};

export const createFeature = async (index, name, value, description = 'description') => {
    await gotoFeatures();
    await t.click('#show-create-feature-btn');
    await setText(byId('featureID'), name);
    await setText(byId('featureDesc'), description);
    if (value) {
        await t.click(byId('toggle-feature-button'));
    }
    await t.click(byId('create-feature-btn'));
    await waitForElementVisible(byId(`feature-item-${index}`));
};

export const deleteFeature = async (index, name) => {
    await t.click(byId(`remove-feature-btn-${index}`));
    await setText('[name="confirm-feature-name"]', name);
    await t.click('#confirm-remove-feature-btn');
    await waitForElementNotExist(`remove-feature-btn-${index}`);
};

export const toggleFeature = async (index, toValue) => {
    await t.click(byId(`feature-switch-${index}${toValue ? '-off' : 'on'}`));
    await t.click('#confirm-toggle-feature-btn');
    await waitForElementVisible(byId(`feature-switch-${index}${toValue ? '-on' : 'off'}`));
};

export default {};
