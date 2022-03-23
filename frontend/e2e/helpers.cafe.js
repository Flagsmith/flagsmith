import { Selector, t } from 'testcafe';

export const byId = id => `[data-test="${id}"]`;

export const setText = async (selector, text) => {
    console.log(`Set text ${selector} : ${text}`);
    return t.selectText(selector)
        .pressKey('delete')
        .selectText(selector) // Prevents issue where input tabs out of focus
        .typeText(selector, `${text}`);
};

export const waitForElementVisible = async (selector) => {
    console.log(`Waiting element visible ${selector}`);
    return t.expect(Selector(selector).visible).ok();
};

export const waitForElementNotExist = async (selector) => {
    console.log(`Waiting element not visible ${selector}`);
    return t.expect(Selector(selector).exists).notOk('', { timeout: 10000 });
};
export const gotoFeatures = async () => {
    await click('#features-link');
    await waitForElementVisible('#show-create-feature-btn');
};

export const click = async (selector) => {
    await waitForElementVisible(selector);
    await t.expect(Selector(selector).hasAttribute('disabled')).notOk('ready for testing', { timeout: 5000 });
    await t.click(selector);
};
export const gotoSegments = async () => {
    await click('#segments-link');
};

export const gotoTraits = async () => {
    await click('#users-link');
    await click(byId('user-item-0'));
    await waitForElementVisible('#add-trait');
};

export const createTrait = async (index, id, value) => {
    await click('#add-trait');
    await waitForElementVisible('#create-trait-modal');
    await setText('[name="traitID"]', id);
    await setText('[name="traitValue"]', value);
    await click('#create-trait-btn');
    await waitForElementVisible(byId(`user-trait-value-${index}`));
    const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
    await assertTextContent(byId(`user-trait-value-${index}`), expectedValue);
};

export const deleteTrait = async (index) => {
    await click(byId(`delete-user-trait-${index}`));
    await click('#confirm-btn-yes');
    await waitForElementNotExist(byId(`user-trait-${index}`));
};

// eslint-disable-next-line no-console
export const log = (message, group = '') => console.log('\n', '\x1b[32m', `${group ? `[${group}] ` : ''}${message}`, '\x1b[0m', '\n');

export const viewFeature = async (index) => {
    await click(byId(`feature-item-${index}`));
    await waitForElementVisible('#create-feature-modal');
};

export const addSegmentOverrideConfig = async (index, value, selectionIndex = 0) => {
    await click(byId('segment_overrides'));
    await click(byId(`select-segment-option-${selectionIndex}`));
    await waitForElementVisible(byId(`segment-override-value-${index}`));
    await setText(byId(`segment-override-value-${0}`), value);
};

export const addSegmentOverride = async (index, value, selectionIndex = 0) => {
    await click(byId('segment_overrides'));
    await click(byId(`select-segment-option-${selectionIndex}`));
    await waitForElementVisible(byId(`segment-override-value-${index}`));
    if (value) {
        await click(`${byId(`segment-override-${0}`)} [role="switch"]`);
    }
};


export const saveFeature = async () => {
    await click('#update-feature-btn');
    await waitForElementVisible('.toast-message');
    await waitForElementNotExist('.toast-message');
    await closeModal()
    await waitForElementNotExist('#create-feature-modal');
};


export const saveFeatureSegments = async () => {
    await click('#update-feature-segments-btn');
    await waitForElementVisible('.toast-message');
    await waitForElementNotExist('.toast-message');
    await closeModal()
    await waitForElementNotExist('#create-feature-modal');
};

export const goToUser = async (index) => {
    await click('#users-link');
    await click(byId(`user-item-${index}`));
};

export const gotoFeature = async (index) => {
    await click(byId(`feature-item-${index}`));
    await waitForElementVisible('#create-feature-modal');
};

export const setSegmentOverrideIndex = async (index, newIndex) => {
    await click(byId('segment_overrides'));
    await setText(byId(`sort-${index}`), `${newIndex}`);
};

export const assertTextContent = (selector, v) => t.expect(Selector(selector).textContent).eql(v);
export const assertTextContentContains = (selector, v) => t.expect(Selector(selector).textContent).contains(v);
export const getText = selector => Selector(selector).innerText;

export const deleteSegment = async (index, name) => {
    await click(byId(`remove-segment-btn-${index}`));
    await setText('[name="confirm-segment-name"]', name);
    await click('#confirm-remove-segment-btn');
    await waitForElementNotExist(`remove-segment-btn-${index}`);
};

export const login = async (email, password) => {
    await setText('[name="email"]', `${email}`);
    await setText('[name="password"]', `${password}`);
    await click('#login-btn');
    await waitForElementVisible('#project-select-page');
};

export const createRemoteConfig = async (index, name, value, description = 'description') => {
    const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
    await gotoFeatures();
    await click('#show-create-feature-btn');
    await setText(byId('featureID'), name);
    await setText(byId('featureValue'), value);
    await setText(byId('featureDesc'), description);
    await click(byId('create-feature-btn'));
    await waitForElementVisible(byId(`feature-value-${index}`));
    await assertTextContent(byId(`feature-value-${index}`), expectedValue);
};
export const closeModal = async ()=> {

    await t.click("body", {
        offsetX: 50,
        offsetY: 50
    })

}
export const createFeature = async (index, name, value, description = 'description') => {
    await gotoFeatures();
    await click('#show-create-feature-btn');
    await setText(byId('featureID'), name);
    await setText(byId('featureDesc'), description);
    if (value) {
        await click(byId('toggle-feature-button'));
    }
    await click(byId('create-feature-btn'));
    await waitForElementVisible(byId(`feature-item-${index}`));
};

export const deleteFeature = async (index, name) => {
    await click(byId(`remove-feature-btn-${index}`));
    await setText('[name="confirm-feature-name"]', name);
    await click('#confirm-remove-feature-btn');
    await waitForElementNotExist(`remove-feature-btn-${index}`);
};

export const toggleFeature = async (index, toValue) => {
    await click(byId(`feature-switch-${index}${toValue ? '-off' : 'on'}`));
    await click('#confirm-toggle-feature-btn');
    await waitForElementVisible(byId(`feature-switch-${index}${toValue ? '-on' : 'off'}`));
};

export const setSegmentRule = async (ruleIndex, orIndex, name, operator, value) => {
    await setText(byId(`rule-${ruleIndex}-property-${orIndex}`), name);
    if (operator) {
        await setText(byId(`rule-${ruleIndex}-operator-${orIndex}`), operator);
    }
    await setText(byId(`rule-${ruleIndex}-value-${orIndex}`), value);
};

export const createSegment = async (index, id, rules) => {
    await click(byId('show-create-segment-btn'));
    await setText(byId('segmentID'), id);
    for (let x = 0; x<rules.length; x++) {
        const rule = rules[x];
        if (x > 0) {
            // eslint-disable-next-line no-await-in-loop
            await click(byId('add-rule'));
        }
        // eslint-disable-next-line no-await-in-loop
        await setSegmentRule(x, 0, rule.name, rule.operator, rule.value);
        for (let orIndex = 0; orIndex<rule.ors; orIndex++) {
            const or = rule.ors[orIndex];
            // eslint-disable-next-line no-await-in-loop
            await click(byId(`rule-${x}-or`));
            // eslint-disable-next-line no-await-in-loop
            await setSegmentRule(x, orIndex + 1, or.name, or.operator, or.value);
        }
    }
    // Create
    await click(byId('create-segment'));
    await waitForElementVisible(byId(`segment-${index}-name`));
    await assertTextContent(byId(`segment-${index}-name`), id);
};
export default {};
