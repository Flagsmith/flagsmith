import {Page} from "@playwright/test";

export const byId = id => `[data-test="${id}"]`;
export const click = async (selector:string,page:Page) =>{
    const el = await page.locator(selector).click()
}
export const setText = async (selector:string, text:string|number, page:Page) =>{
    if(text === null || typeof text === "undefined") {
        await page.locator(selector).fill("")
    } else {
        await page.locator(selector).fill(`${text}`)
    }
}

export const waitForElementVisible = async (selector:string, page:Page, first?:boolean) =>{
    if(first) {
        await page.locator(selector).first().waitFor({state:"visible", timeout: 10000})
    } else {
        await page.locator(selector).first().waitFor({state:"visible", timeout:10000})
    }
}
export const waitForElementNotExist = async (selector:string, page:Page, first?:boolean) =>{
    if (first) {
        await page.locator(selector).first().waitFor({state:'detached', timeout: 10000})
    } else {
        await page.locator(selector).waitFor({state:'detached', timeout: 10000})
    }
}
export const assertTextContent = async (selector:string, value, page:Page) =>{
    await page.textContent(selector,value)
}
export const closeModal = async (page:Page) => {
    await page.click('body', {
        position: {
            x: 50,
            y: 50,
        }
    });
};
export const gotoFeatures = async (page:Page) => {
    await click('#features-link', page);
    await page.waitForTimeout(500)
    await waitForElementVisible('#show-create-feature-btn', page);
    await page.waitForTimeout(500)
};

export const createRemoteConfig = async (page:Page, index:number, name:string, value:string|number, description = 'description', defaultOff:boolean=false, mvs:{weight:number, value:string}[] = []) => {
    const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
    await gotoFeatures(page);
    await click('#show-create-feature-btn', page);
    await setText(byId('featureID'), name, page);
    await setText(byId('featureValue'), value, page);
    await setText(byId('featureDesc'), description,page);
    if (!defaultOff) {
        await click(byId('toggle-feature-button'),page);
    }
    for (let i = 0; i < mvs.length; i++) {
        const v = mvs[i]
        await click(byId('add-variation'),page);
        await setText(byId(`featureVariationValue${i}`), v.value, page);
        await setText(byId(`featureVariationWeight${v.value}`), `${v.weight}` , page);
    }
    await click(byId('create-feature-btn'),page);
    await waitForElementVisible(byId(`feature-value-${index}`),page);
    await assertTextContent(byId(`feature-value-${index}`), expectedValue, page);
};

export const toggleFeature = async (index, toValue, page) => {
    await click(byId(`feature-switch-${index}${toValue ? '-off' : 'on'}`), page);
    await click('#confirm-toggle-feature-btn', page);
    await waitForElementVisible(byId(`feature-switch-${index}${toValue ? '-on' : 'off'}`), page);
};
export const getText = async (selector, page:Page) => {
    return await page.locator(selector).textContent()
};
export const getInputValue  = async (selector, page:Page) => {
    return await page.locator(selector).inputValue()
};
export const deleteFeature = async (page:Page, index:number, name:string) => {
    await click(byId(`remove-feature-btn-${index}`), page);
    await setText('[name="confirm-feature-name"]', name, page);
    await click('#confirm-remove-feature-btn', page);
    await waitForElementNotExist(`remove-feature-btn-${index}`, page);
};

export const gotoSegments = async (page:Page) => {
    await click('#segments-link', page);
};

export const setSegmentRule = async (page:Page, ruleIndex:number, orIndex:number, name:string, operator:string, value:string|number) => {
    await setText(byId(`rule-${ruleIndex}-property-${orIndex}`), name, page);
    if (operator) {
        await setText(byId(`rule-${ruleIndex}-operator-${orIndex}`), operator,page);
    }
    await setText(byId(`rule-${ruleIndex}-value-${orIndex}`), value,page);
};


export const createSegment = async (page:Page, index:number, id:string, rules:{name:string, operator:string, value:string|number, ors?:{name:string, operator:string, value:string|number}[]} []) => {
    await click(byId('show-create-segment-btn'),page);
    await setText(byId('segmentID'), id,page);
    for (let x = 0; x<rules.length; x++) {
        const rule = rules[x];
        if (x > 0) {
            // eslint-disable-next-line no-await-in-loop
            await click(byId('add-rule'),page);
        }
        // eslint-disable-next-line no-await-in-loop
        await setSegmentRule(page,x, 0, rule.name, rule.operator, rule.value);
        if(rule.ors) {
            for (let orIndex = 0; orIndex<rule.ors.length; orIndex++) {
                const or = rule.ors[orIndex];
                // eslint-disable-next-line no-await-in-loop
                await click(byId(`rule-${x}-or`),page);
                // eslint-disable-next-line no-await-in-loop
                await setSegmentRule(page,x, orIndex + 1, or.name, or.operator, or.value);
            }
        }
    }
    // Create
    await click(byId('create-segment'),page);
    await waitForElementVisible(byId(`segment-${index}-name`),page);
    await assertTextContent(byId(`segment-${index}-name`), id, page);
};

export const createFeature = async (page:Page, index:number, name:string, value?:boolean, description = 'description') => {
    await gotoFeatures(page);
    await click('#show-create-feature-btn', page);
    await setText(byId('featureID'), name, page);
    await setText(byId('featureDesc'), description,page);
    if (value) {
        await click(byId('toggle-feature-button'), page);
    }
    await click(byId('create-feature-btn'),page);
    await waitForElementVisible(byId(`feature-item-${index}`), page);
};

export const gotoTraits = async (page:Page) => {
    await click('#users-link',page);
    await click(byId('user-item-0'),page);
    await waitForElementVisible('#add-trait',page);
};

export const createTrait = async (index:number, id:string, value:string|number,page:Page) => {
    await click('#add-trait',page);
    await waitForElementVisible('#create-trait-modal',page);
    await setText('[name="traitID"]', id,page);
    await setText('[name="traitValue"]', value,page);
    await click('#create-trait-btn',page);
    await page.waitForTimeout(1000);
    await waitForElementVisible(byId(`user-trait-value-${index}`),page);
    const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
    await assertTextContent(byId(`user-trait-value-${index}`), expectedValue,page);
};

export const deleteTrait = async (page:Page, index:number) => {
    await click(byId(`delete-user-trait-${index}`),page);
    await click('#confirm-btn-yes',page);
    await waitForElementNotExist(byId(`user-trait-${index}`),page);
};


export const viewFeature = async (index:number, page:Page) => {
    await click(byId(`feature-item-${index}`),page);
    await waitForElementVisible('#create-feature-modal',page);
};

export const addSegmentOverrideConfig = async (page:Page,index:number, value:string|number, selectionIndex = 0) => {
    await click(byId('segment_overrides'),page);
    await click(byId(`select-segment-option-${selectionIndex}`),page);

    await waitForElementVisible(byId(`segment-override-value-${index}`),page);
    await setText(byId(`segment-override-value-${0}`), value,page);
    await click(byId('segment-override-toggle-0'),page);
};

export const addSegmentOverride = async (page:Page, index:number, value:boolean, selectionIndex = 0, mvs?:{value:string|number, weight:number}[]) => {
    await click(byId('segment_overrides'),page);
    await click(byId(`select-segment-option-${selectionIndex}`),page);
    await waitForElementVisible(byId(`segment-override-value-${index}`),page);
    if (value) {
        await click(`${byId(`segment-override-${0}`)} [role="switch"]`,page);
    }
    if (mvs) {
        await Promise.all(mvs.map(async (v, i) => {
            await setText(`.segment-overrides ${byId(`featureVariationWeight${v.value}`)}`, v.weight,page);
        }));
    }
};

export const saveFeature = async (page:Page) => {
    await click('#update-feature-btn',page);
    await waitForElementVisible('.toast-message',page, true);
    await waitForElementNotExist('.toast-message',page, true);
    await closeModal(page);
    await waitForElementNotExist('#create-feature-modal',page);
};

export const deleteSegment = async (index:number, name:string, page:Page) => {
    await click(byId(`remove-segment-btn-${index}`),page);
    await setText('[name="confirm-segment-name"]', name,page);
    await click('#confirm-remove-segment-btn',page);
    await waitForElementNotExist(`remove-segment-btn-${index}`,page);
};

export const login = async (email:string, password:string, page:Page) => {
    await setText('[name="email"]', `${email}`,page);
    await setText('[name="password"]', `${password}`,page);
    await click('#login-btn',page);
    await waitForElementVisible('#project-select-page',page);
};

export const saveFeatureSegments = async (page:Page) => {
    await click('#update-feature-segments-btn',page);
    await waitForElementVisible('.toast-message',page, true);
    await waitForElementNotExist('.toast-message',page, true);
    await closeModal(page);
    await waitForElementNotExist('#create-feature-modal',page);
};

export const goToUser = async (index:number,page:Page) => {
    await click('#users-link',page);
    await click(byId(`user-item-${index}`),page);
};

export const gotoFeature = async (index:number, page:Page) => {
    await click(byId(`feature-item-${index}`),page);
    await waitForElementVisible('#create-feature-modal',page);
};

export const setSegmentOverrideIndex = async (index:number, newIndex:number, page:Page) => {
    await click(byId('segment_overrides'),page);
    await setText(byId(`sort-${index}`), `${newIndex}`,page);
};


export const log = (message, group = '') => console.log('\n', '\x1b[32m', `${group ? `[${group}] ` : ''}${message}`, '\x1b[0m', '\n');
