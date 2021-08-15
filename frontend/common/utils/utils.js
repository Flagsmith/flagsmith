module.exports = Object.assign({}, require('./base/_utils'), {
    numberWithCommas(x) {
        return x.toString()
            .replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    escapeHtml(html) {
        const text = document.createTextNode(html);
        const p = document.createElement('p');
        p.appendChild(text);
        return p.innerHTML;
    },

    calculateControl(multivariateOptions, variations) {
        if (!multivariateOptions || !multivariateOptions.length) {
            return 100;
        }
        let total = 0;
        multivariateOptions.map((v) => {
            const variation = variations && variations.find(env => env.multivariate_feature_option === v.id);
            total += variation ? variation.percentage_allocation : v.default_percentage_allocation;
            return null;
        });
        return 100 - total;
    },
    featureStateToValue(featureState) {
        if (!featureState) {
            return null;
        }

        return Utils.getTypedValue(featureState.integer_value || featureState.string_value || featureState.boolean_value);
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
            string_value: val || '',
        };
    },
    getFlagValue(projectFlag, environmentFlag, identityFlag) {
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
            };
        }
        return {
            type: projectFlag.type,
            name: projectFlag.name,
            tags: projectFlag.tags,
            hide_from_client: environmentFlag.hide_from_client,
            feature_state_value: environmentFlag.feature_state_value,
            multivariate_options: projectFlag.multivariate_options,
            enabled: environmentFlag.enabled,
            description: projectFlag.description,
        };
    },

    getTypedValue(str) {
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


        if (str == 'true') {
            return true;
        }
        if (str == 'false') {
            return false;
        }

        if (isNum) {
            if (str.indexOf('.') != -1) {
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

    getPlansPermission: (plans, permission) => {
        if (!plans || !plans.length) {
            return false;
        }
        const found = _.find(
            plans.map(plan => Utils.getPlanPermission(plan, permission)),
            perm => !!perm,
        );
        return !!found;
    },
    getPlanPermission: (plan, permission) => {
        let valid = true;
        if (!plan) {
            return false;
        }
        const date = AccountStore.getDate();
        const cutOff = moment('03-11-20', 'DD-MM-YY');
        if (date && moment(date)
            .valueOf() < cutOff.valueOf()) {
            return true;
        }
        switch (permission) {
            case '2FA': {
                valid = !plan.includes('side-project');
                break;
            }
            case 'RBAC': {
                valid = !plan.includes('side-project');
                break;
            }
            case 'AUDIT': {
                valid = !plan.includes('side-project') && !plan.includes('startup');
                break;
            }
            default:
                valid = true;
                break;
        }
        return valid;
    },

    getPlanName: (plan) => {
        switch (plan) {
            case 'side-project':
            case 'side-project-annual':
                return 'Side Project';
            case 'startup':
            case 'startup-annual':
            case 'startup-v2':
            case 'startup-v2-annual':
                return 'Startup';
            case 'scale-up':
            case 'scale-up-annual':
            case 'scale-up-v2':
            case 'scale-up-v2-annual':
                return 'Scale-Up';
            case 'enterprise':
            case 'enterprise-annual':
                return 'Enterprise';
            default:
                return 'Free';
        }
    },
});
