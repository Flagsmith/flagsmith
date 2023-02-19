const React = require('react');
const semver = require('semver');
const ProjectStore = require('../../common/stores/project-store');

let flagsmithBetaFeatures = null;
const planNames = {
    free: 'Free',
    scaleUp: 'Scale-Up',
    sideProject: 'Side Project',
    startup:  'Startup',
    enterprise:  'Enterprise'
}
module.exports = Object.assign({}, require('./base/_utils'), {
    numberWithCommas(x) {
        return x.toString()
            .replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    loadScriptPromise(url) {
        return new Promise((resolve, reject) => {
            const cb = function () {
                this.removeEventListener('load', cb);
                resolve(null);
            };
            const head = document.getElementsByTagName('head')[0];
            const script = document.createElement('script');
            script.type = 'text/javascript';
            script.addEventListener('load', cb);
            script.src = url;
            head.appendChild(script);
        });
    },

    changeRequestsEnabled(value) {
        return typeof value === 'number';
    },

    escapeHtml(html) {
        const text = document.createTextNode(html);
        const p = document.createElement('p');
        p.appendChild(text);
        return p.innerHTML;
    },
    getApproveChangeRequestPermission() {
        if (Utils.getFlagsmithHasFeature('update_feature_state_permission')) {
            return 'APPROVE_CHANGE_REQUEST';
        }
        return 'VIEW_ENVIRONMENT';
    },
    getViewIdentitiesPermission() {
        if (Utils.getFlagsmithHasFeature('view_identities_permission')) {
            return 'VIEW_IDENTITIES';
        }
        return 'MANAGE_IDENTITIES';
    },
    getManageFeaturePermission(isChangeRequest, isUser) {
        if (isChangeRequest && Utils.getFlagsmithHasFeature('update_feature_state_permission')) {
            return 'CREATE_CHANGE_REQUEST';
        }
        if (Utils.getFlagsmithHasFeature('update_feature_state_permission')) {
            return 'UPDATE_FEATURE_STATE';
        }
        return 'ADMIN';
    },
    getManageFeaturePermissionDescription(isChangeRequest, user) {
        if (isChangeRequest && Utils.getFlagsmithHasFeature('update_feature_state_permission')) {
            return 'Create Change Request';
        }
        if (Utils.getFlagsmithHasFeature('update_feature_state_permission')) {
            return 'Update Feature State';
        }
        return 'Admin';
    },
    getManageUserPermission() {
        return 'MANAGE_IDENTITIES';
    },
    getManageUserPermissionDescription() {
        return 'Manage Identities';
    },
    getTraitEndpointMethod() {
        if (Utils.getFlagsmithHasFeature('edge_identities') && ProjectStore.model && ProjectStore.model.use_edge_identities) {
            return 'put';
        }
        return 'post';
    },
    getIsEdge() {
        if (Utils.getFlagsmithHasFeature('edge_identities') && ProjectStore.model && ProjectStore.model.use_edge_identities) {
            return true;
        }
        return false;
    },
    openChat() {
        if (typeof $crisp !== 'undefined') {
            $crisp.push(['do', 'chat:open']);
        }
        if (window.zE) {
            zE('messenger', 'open');
        }
    },
    isMigrating() {
        if (Utils.getFlagsmithHasFeature('edge_identities') && ProjectStore.model && (ProjectStore.model.migration_status === 'MIGRATION_IN_PROGRESS' || ProjectStore.model.migration_status === 'MIGRATION_SCHEDULED')) {
            return true;
        }
        return false;
    },
    getUpdateTraitEndpoint(environmentId, userId) {
        if (Utils.getFlagsmithHasFeature('edge_identities') && ProjectStore.model && ProjectStore.model.use_edge_identities) {
            return `${Project.api}environments/${environmentId}/edge-identities/${userId}/update-traits/`;
        }
        return `${Project.api}traits/`;
    },
    getTraitEndpoint(environmentId, userId) {
        if (Utils.getFlagsmithHasFeature('edge_identities') && ProjectStore.model && ProjectStore.model.use_edge_identities) {
            return `${Project.api}environments/${environmentId}/edge-identities/${userId}/list-traits/`;
        }
        return `${Project.api}environments/${environmentId}/identities/${userId}/traits/`;
    },
    removeElementFromArray(array, index) {
        return array.slice(0, index).concat(array.slice(index + 1));
    },
    findOperator(operator, value, operators) {
        const findAppended = `${value}`.includes(':') ? (operators || []).find((v) => {
            const split = value.split(':');
            const targetKey = `:${split[split.length - 1]}`;
            return v.value === operator + targetKey;
        }) : false;
        if (findAppended) return findAppended;

        return operators.find(v => v.value === operator);
    },
    validateRule(rule) {
        if (!rule) return false;

        const operators = Utils.getFlagsmithValue('segment_operators') ? JSON.parse(Utils.getFlagsmithValue('segment_operators')) : [];
        const operatorObj = Utils.findOperator(rule.operator, rule.value, operators);

        if (operatorObj && operatorObj.value && operatorObj.value.toLowerCase().includes('semver')) {
            return !!semver.valid(`${rule.value.split(':')[0]}`);
        }

        switch (rule.operator) {
            case 'PERCENTAGE_SPLIT': {
                const value = parseFloat(rule.value);
                return !isNaN(value) && value >= 0 && value <= 100;
            }
            case 'REGEX': {
                try {
                    if (!rule.value) {
                        throw new Error('');
                    }
                    new RegExp(`${rule.value}`);
                    return true;
                } catch (e) {
                    return false;
                }
            }
            case 'MODULO': {
                const valueSplit = rule.value.split('|');
                if (valueSplit.length === 2) {
                    const [divisor, remainder] = [parseFloat(valueSplit[0]), parseFloat(valueSplit[1])];
                    return (!isNaN(divisor) && divisor > 0) && (!isNaN(remainder) && remainder >= 0);
                }
                return false;
            }
            default:
                return (operatorObj && operatorObj.hideValue) || (rule.value !== '' && rule.value !== undefined && rule.value !== null);
        }
    },

    getShouldSendIdentityToTraits(_project) {
        const project = _project || ProjectStore.model;
        if (Utils.getFlagsmithHasFeature('edge_identities') && project && project.use_edge_identities) {
            return false;
        }
        return true;
    },
    getShouldUpdateTraitOnDelete(_project) {
        const project = _project || ProjectStore.model;
        if (Utils.getFlagsmithHasFeature('edge_identities') && project && project.use_edge_identities) {
            return true;
        }
        return false;
    },

    getShouldShowProjectTraits(_project) {
        const project = _project || ProjectStore.model;
        if (Utils.getFlagsmithHasFeature('edge_identities') && project && project.use_edge_identities) {
            return false;
        }
        return true;
    },

    getIdentitiesEndpoint(_project) {
        const project = _project || ProjectStore.model;
        if (Utils.getFlagsmithHasFeature('edge_identities') && project && project.use_edge_identities) {
            return 'edge-identities';
        }
        return 'identities';
    },

    getSDKEndpoint(_project) {
        const project = _project || ProjectStore.model;

        if (Utils.getFlagsmithHasFeature('edge_identities') && project && project.use_edge_identities) {
            return Project.flagsmithClientEdgeAPI;
        }
        return Project.api;
    },

    getShouldHideIdentityOverridesTab(_project) {
        const project = _project || ProjectStore.model;
        if (Utils.getFlagsmithHasFeature('edge_identities') && project && project.use_edge_identities) {
            return true;
        }
        return false;
    },

    getFeatureStatesEndpoint(_project) {
        const project = _project || ProjectStore.model;
        if (Utils.getFlagsmithHasFeature('edge_identities') && project && project.use_edge_identities) {
            return 'edge-featurestates';
        }
        return 'featurestates';
    },

    parseBetaFeatures() {
        if (!flagsmith.hasFeature('beta_features')) {
            return [];
        } if (flagsmithBetaFeatures) {
            return flagsmithBetaFeatures;
        }
        let res;
        try {
            res = JSON.parse(flagsmith.getValue('beta_features'));
            const features = [];
            Object.keys(res).map((v) => {
                res[v].map((v) => {
                    features.push(v.flag);
                });
            });
            flagsmithBetaFeatures = features;
        } catch (e) {

        }
        return flagsmithBetaFeatures || [];
    },

    getFlagsmithValue(key) {
        const betaFeatures = Utils.parseBetaFeatures();
        if (betaFeatures.includes(key)) {
            if (typeof flagsmith.getTrait(`${key}-opt-in-value`) !== 'undefined') {
                return flagsmith.getTrait(`${key}-opt-in-value`);
            }
        }
        return flagsmith.getValue(key);
    },

    getFlagsmithHasFeature(key) {
        const betaFeatures = Utils.parseBetaFeatures();
        if (betaFeatures.includes(key)) {
            if (typeof flagsmith.getTrait(`${key}-opt-in-enabled`) === 'boolean') {
                return flagsmith.getTrait(`${key}-opt-in-enabled`);
            }
        }
        return flagsmith.hasFeature(key);
    },

    renderWithPermission(permission, name, el) {
        return permission ? (
            el
        ) : (
            <Tooltip
              title={<div>{el}</div>}
              place="right"
              html
            >{name}
            </Tooltip>
        );
    },


    calculateControl(multivariateOptions, variations) {
        if (!multivariateOptions || !multivariateOptions.length) {
            return 100;
        }
        let total = 0;
        multivariateOptions.map((v) => {
            const variation = variations && variations.find(env => env.multivariate_feature_option === v.id);
            total += variation ? variation.percentage_allocation : typeof v.default_percentage_allocation === 'number' ? v.default_percentage_allocation : v.percentage_allocation;
            return null;
        });
        return 100 - total;
    },
    featureStateToValue(featureState) {
        if (!featureState) {
            return null;
        }

        if (typeof featureState.integer_value === 'number') {
            return Utils.getTypedValue(featureState.integer_value);
        } if (typeof featureState.float_value === 'number') {
            return Utils.getTypedValue(featureState.float_value);
        }

        return Utils.getTypedValue(featureState.string_value || featureState.boolean_value);
    },
    valueToFeatureState(value) {
        const val = Utils.getTypedValue(value);

        if (typeof val === 'boolean') {
            return {
                type: 'bool',
                boolean_value: val,
                integer_value: null,
                string_value: null,
            };
        }

        if (typeof val === 'number') {
            return {
                type: 'int',
                boolean_value: null,
                integer_value: val,
                string_value: null,
            };
        }

        return {
            type: 'unicode',
            boolean_value: null,
            integer_value: null,
            string_value: value === null ? null : val || '',
        };
    },
    getFlagValue(projectFlag, environmentFlag, identityFlag, multivariate_options) {
        if (!environmentFlag) {
            return {
                name: projectFlag.name,
                type: projectFlag.type,
                feature_state_value: projectFlag.initial_value,
                multivariate_options: projectFlag.multivariate_options,
                tags: projectFlag.tags,
                enabled: false,
                hide_from_client: false,
                description: projectFlag.description,
                is_archived: projectFlag.is_archived,
            };
        }
        if (identityFlag) {
            return {
                type: projectFlag.type,
                name: projectFlag.name,
                multivariate_options: projectFlag.multivariate_options,
                feature_state_value: identityFlag.feature_state_value,
                hide_from_client: environmentFlag.hide_from_client,
                enabled: identityFlag.enabled,
                description: projectFlag.description,
                is_archived: projectFlag.is_archived,
            };
        }
        return {
            type: projectFlag.type,
            name: projectFlag.name,
            tags: projectFlag.tags,
            hide_from_client: environmentFlag.hide_from_client,
            feature_state_value: environmentFlag.feature_state_value,
            multivariate_options: projectFlag.multivariate_options.map((v) => {
                const matching = multivariate_options && multivariate_options.find(m => v.id === m.multivariate_feature_option);
                return {
                    ...v,
                    default_percentage_allocation: matching ? matching.percentage_allocation : v.default_percentage_allocation,
                };
            }),
            enabled: environmentFlag.enabled,
            description: projectFlag.description,
            is_archived: projectFlag.is_archived,
        };
    },

    getTypedValue(str, boolToString) {
        if (typeof str === 'undefined') {
            return '';
        }
        if (typeof str !== 'string') {
            return str;
        }

        const isNum = /^\d+$/.test(str);

        if (isNum && parseInt(str) > Number.MAX_SAFE_INTEGER) {
            return `${str}`;
        }


        if (str === 'true') {
            if (boolToString) return 'true';
            return true;
        }
        if (str === 'false') {
            if (boolToString) return 'false';
            return false;
        }

        if (isNum) {
            if (str.indexOf('.') !== -1) {
                return parseFloat(str);
            }
            return parseInt(str);
        }

        return str;
    },

    scrollToTop: (timeout = 500) => {
        $('html,body')
            .animate({ scrollTop: 0 }, timeout);
    },

    scrollToElement: (selector, timeout = 500) => {
        const el = $(selector);
        if (!el || !el.offset) return;
        $('html,body')
            .animate({ scrollTop: el.offset().top }, timeout);
    },

    scrollToSignUp: () => {
        Utils.scrollToElement('.signup-form');
    },

    getPlansPermission: (permission) => {
        if (!Utils.getFlagsmithHasFeature('plan_based_access')) {
            return true;
        }
        const isOrgPermission = permission !== '2FA';
        const plans = isOrgPermission ? AccountStore.getActiveOrgPlan() ? [AccountStore.getActiveOrgPlan()] : null
            : AccountStore.getPlans();

        if (!plans || !plans.length) {
            return false;
        }
        const found = _.find(
            plans.map(plan => Utils.getPlanPermission(plan, permission)),
            perm => !!perm,
        );
        return !!found;
    },
    appendImage: (src) => {
        const img = document.createElement('img');
        img.src = src;
        document.body.appendChild(img);
    },
    getPlanPermission: (plan, permission) => {
        let valid = true;
        const planName = Utils.getPlanName(plan)
        if (!Utils.getFlagsmithHasFeature('plan_based_access')) {
            return true;
        }
        if (!plan || planName === planNames.free) {
            return false;
        }
        const date = AccountStore.getDate();
        const cutOff = moment('03-11-20', 'DD-MM-YY');
        // if (date && moment(date)
        //     .valueOf() < cutOff.valueOf()) {
        //     return true;
        // }
        const isSideProjectOrGreater = planName !== planNames.sideProject;
        const isScaleupOrGreater = isSideProjectOrGreater && planName!== planNames.startup;
        switch (permission) {
            case 'FLAG_OWNERS': {
                valid = isScaleupOrGreater;
                break;
            }
            case 'CREATE_ADDITIONAL_PROJECT': {
                valid = isSideProjectOrGreater;
                break;
            }
            case '2FA': {
                valid = isSideProjectOrGreater;
                break;
            }
            case 'RBAC': {
                valid = isSideProjectOrGreater;
                break;
            }
            case 'AUDIT': {
                valid = isScaleupOrGreater;
                break;
            }
            case 'AUTO_SEATS': {
                valid = isScaleupOrGreater && Utils.getFlagsmithHasFeature('auto_seats');
                break;
            }
            case 'FORCE_2FA': {
                valid = isScaleupOrGreater;
                break;
            }
            case 'SCHEDULE_FLAGS': {
                valid = isSideProjectOrGreater;
                break;
            }
            case '4_EYES': {
                valid = isScaleupOrGreater;
                break;
            }
            default:
                valid = true;
                break;
        }
        return valid;
    },

    getPlanName: (plan) => {
        if (plan && plan.includes("scale-up")) {
            return planNames.scaleUp;
        }
        if (plan && plan.includes("side-project")) {
            return planNames.sideProject;
        }
        if (plan && plan.includes("startup")) {
            return planNames.startup;
        }
        if (plan && plan.includes("enterprise")) {
            return planNames.enterprise;
        }
        return planNames.free
    },
});
