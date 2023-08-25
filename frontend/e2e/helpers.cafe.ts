import { RequestLogger, Selector, t } from 'testcafe';
import { Operator } from 'rxjs';

export const LONG_TIMEOUT = 40000

export const byId = (id:string) => `[data-test="${id}"]`;

export type MultiVariate = {value:string,weight:number}

export type Rule = {
    name: string,
    operator: string,
    value: string | number | boolean,
    ors?:Rule[]
}
export const setText = async (selector:string, text:string) => {
    console.log(`Set text ${selector} : ${text}`);
    return t.selectText(selector)
        .pressKey('delete')
        .selectText(selector) // Prevents issue where input tabs out of focus
        .typeText(selector, `${text}`);
};

export const waitForElementVisible = async (selector:string) => {
    console.log(`Waiting element visible ${selector}`);
    return t.expect(Selector(selector).visible).ok(`waitForElementVisible(${selector})`, { timeout: LONG_TIMEOUT });
};

export const logResults = async (requests:LoggedRequest[], t)=> {
    if(!t.testRun?.errs?.length) {
        return // do not log anything for passed tests
    }
    console.log(JSON.stringify(requests.filter((v)=>{
        if(v.request?.url?.includes("get-subscription-metadata") || v.request?.url?.includes("analytics/flags")) {
            return false
        }
        if (v.response && (v.response?.statusCode >= 200 && v.response?.statusCode < 300)) {
            return false
        }
        return true
    }), null, 2));
    console.log("Session JavaScript Errors")
    console.log(JSON.stringify((await t.getBrowserConsoleMessages())));
}

export const waitForElementNotExist = async (selector:string) => {
    console.log(`Waiting element not visible ${selector}`);
    return t.expect(Selector(selector).exists).notOk('', { timeout: 10000 });
};
export const gotoFeatures = async () => {
    await click('#features-link');
    await waitForElementVisible('#show-create-feature-btn');
};

export const click = async (selector:string) => {
    const field = Selector('input#developer-name[type="text"]')
        .with({visibilityCheck: true})
        .nth(0)
    await waitForElementVisible(selector);
    await t
        .expect(Selector(selector).hasAttribute('disabled'))
        .notOk('ready for testing', { timeout: 5000 })
        .hover(selector)
        .click(selector);
};

export const gotoSegments = async () => {
    await click('#segments-link');
};

export const getLogger = () => RequestLogger(/api\/v1/, {
    logResponseBody: true,
    stringifyRequestBody: true,
    stringifyResponseBody: true,
    logResponseHeaders: true,
    logRequestBody: true,
    logRequestHeaders: true
});

export const gotoTraits = async () => {
    await click('#users-link');
    await click(byId('user-item-0'));
    await waitForElementVisible('#add-trait');
};

export const createTrait = async (index:number, id: string, value:string|boolean|number) => {
    await click('#add-trait');
    await waitForElementVisible('#create-trait-modal');
    await setText('[name="traitID"]', id);
    await setText('[name="traitValue"]', `${value}`);
    await click('#create-trait-btn');
    await t.wait(2000);
    await t.eval(() => location.reload());
    await waitForElementVisible(byId(`user-trait-value-${index}`));
    const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
    await assertTextContent(byId(`user-trait-value-${index}`), expectedValue);
};

export const deleteTrait = async (index:number) => {
    await click(byId(`delete-user-trait-${index}`));
    await click('#confirm-btn-yes');
    await waitForElementNotExist(byId(`user-trait-${index}`));
};

// eslint-disable-next-line no-console
export const log = (message:string, group) => console.log('\n', '\x1b[32m', `${group ? `[${group}] ` : ''}${message}`, '\x1b[0m', '\n');

export const viewFeature = async (index:number) => {
    await click(byId(`feature-item-${index}`));
    await waitForElementVisible('#create-feature-modal');
};

export const addSegmentOverrideConfig = async (index:number, value:string|boolean|number, selectionIndex = 0) => {
    await click(byId('segment_overrides'));
    await click(byId(`select-segment-option-${selectionIndex}`));

    await waitForElementVisible(byId(`segment-override-value-${index}`));
    await setText(byId(`segment-override-value-${0}`), `${value}`);
    await click(byId('segment-override-toggle-0'));
};

export const addSegmentOverride = async (index:number, value:string|boolean|number, selectionIndex = 0, mvs:MultiVariate[] = []) => {
    await click(byId('segment_overrides'));
    await click(byId(`select-segment-option-${selectionIndex}`));
    await waitForElementVisible(byId(`segment-override-value-${index}`));
    if (value) {
        await click(`${byId(`segment-override-${0}`)} [role="switch"]`);
    }
    if (mvs) {
        await Promise.all(mvs.map(async (v, i) => {
            await setText(`.segment-overrides ${byId(`featureVariationWeight${v.value}`)}`, `${v.weight}`);
        }));
    }
};

export const saveFeature = async () => {
    await click('#update-feature-btn');
    await waitForElementVisible('.toast-message');
    await waitForElementNotExist('.toast-message');
    await closeModal();
    await waitForElementNotExist('#create-feature-modal');
};


export const saveFeatureSegments = async () => {
    await click('#update-feature-segments-btn');
    await waitForElementVisible('.toast-message');
    await waitForElementNotExist('.toast-message');
    await closeModal();
    await waitForElementNotExist('#create-feature-modal');
};

export const goToUser = async (index:number) => {
    await click('#users-link');
    await click(byId(`user-item-${index}`));
};

export const gotoFeature = async (index:number) => {
    await click(byId(`feature-item-${index}`));
    await waitForElementVisible('#create-feature-modal');
};

export const setSegmentOverrideIndex = async (index:number, newIndex:number) => {
    await click(byId('segment_overrides'));
    await setText(byId(`sort-${index}`), `${newIndex}`);
};

export const assertTextContent = (selector:string, v:string) => t.expect(Selector(selector).textContent).eql(v);
export const assertTextContentContains = (selector:string, v:string) => t.expect(Selector(selector).textContent).contains(v);
export const getText = (selector:string) => Selector(selector).innerText;

export const deleteSegment = async (index:number, name:string) => {
    await click(byId(`remove-segment-btn-${index}`));
    await setText('[name="confirm-segment-name"]', name);
    await click('#confirm-remove-segment-btn');
    await waitForElementNotExist(`remove-segment-btn-${index}`);
};

export const login = async (email:string, password:string) => {
    await setText('[name="email"]', `${email}`);
    await setText('[name="password"]', `${password}`);
    await click('#login-btn');
    await waitForElementVisible('#project-select-page');
};
export const logout = async () => {
    await click('#account-settings-link');
    await click('#logout-link');
    await waitForElementVisible('#login-page');
};

export const createRemoteConfig = async (index:number, name:string, value:string|number|boolean, description = 'description', defaultOff?:boolean, mvs:MultiVariate[] = []) => {
    const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
    await gotoFeatures();
    await click('#show-create-feature-btn');
    await setText(byId('featureID'), name);
    await setText(byId('featureValue'), `${value}`);
    await setText(byId('featureDesc'), description);
    if (!defaultOff) {
        await click(byId('toggle-feature-button'));
    }
    await Promise.all(mvs.map(async (v, i) => {
        await click(byId('add-variation'));

        await setText(byId(`featureVariationValue${i}`), v.value);
        await setText(byId(`featureVariationWeight${v.value}`), `${v.weight}`);
    }));
    await click(byId('create-feature-btn'));
    await waitForElementVisible(byId(`feature-value-${index}`));
    await assertTextContent(byId(`feature-value-${index}`), expectedValue);
};
export const closeModal = async () => {
    await t.click('body', {
        offsetX: 50,
        offsetY: 50,
    });
};
export const createFeature = async (index:number, name:string, value?:string|boolean|number, description = 'description') => {
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

export const deleteFeature = async (index:number, name:string) => {
    await click(byId(`remove-feature-btn-${index}`));
    await setText('[name="confirm-feature-name"]', name);
    await click('#confirm-remove-feature-btn');
    await waitForElementNotExist(`remove-feature-btn-${index}`);
};

export const toggleFeature = async (index:number, toValue:boolean) => {
    await click(byId(`feature-switch-${index}${toValue ? '-off' : 'on'}`));
    await click('#confirm-toggle-feature-btn');
    await waitForElementVisible(byId(`feature-switch-${index}${toValue ? '-on' : 'off'}`));
};

export const setSegmentRule = async (ruleIndex:number, orIndex:number, name:string, operator:string, value:string|number|boolean) => {
    await setText(byId(`rule-${ruleIndex}-property-${orIndex}`), name);
    if (operator) {
        await setText(byId(`rule-${ruleIndex}-operator-${orIndex}`), operator);
    }
    await setText(byId(`rule-${ruleIndex}-value-${orIndex}`), `${value}`);
};

export const createSegment = async (index:number, id:string, rules?:Rule[]) => {
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
            if( rule.ors) {
                for (let orIndex = 0; orIndex<rule.ors.length; orIndex++) {
                    const or = rule.ors[orIndex];
                    // eslint-disable-next-line no-await-in-loop
                    await click(byId(`rule-${x}-or`));
                    // eslint-disable-next-line no-await-in-loop
                    await setSegmentRule(x, orIndex + 1, or.name, or.operator, or.value);
                }
            }
        }

    // Create
    await click(byId('create-segment'));
    await waitForElementVisible(byId(`segment-${index}-name`));
    await assertTextContent(byId(`segment-${index}-name`), id);
};

export const waitAndRefresh = async (waitFor = 3000) => {
    console.log(`Waiting for ${waitFor}ms, then refreshing.`);
    await t.wait(waitFor);
    await t.eval(() => location.reload());
};

export default {};
