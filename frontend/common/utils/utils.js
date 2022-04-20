const React = require('react');
const ProjectStore = require('../../common/stores/project-store')
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

    getManageFeaturePermission() {
        if (flagsmith.hasFeature('update_feature_state_permission')) {
            return 'UPDATE_FEATURE_STATE';
        }
        return 'ADMIN';
    },

    getIdentitiesEndpoint() {
      if (flagsmith.hasFeature("edge_identities") && ProjectStore.model && ProjectStore.model.use_edge_identities) {
          return "edge-identities"
      }
      return "identities"
    },

    getSDKEndpoint() {
      if (flagsmith.hasFeature("edge_identities") && ProjectStore.model && ProjectStore.model.use_edge_identities) {
          return Project.flagsmithClientEdgeAPI
      }
      return Project.api
    },

    getFeatureStatesEndpoint() {
      if (flagsmith.hasFeature("edge_identities") && ProjectStore.model && ProjectStore.model.use_edge_identities) {
          return "edge-featurestates"
      }
      return "featurestates"
    },

    getManageFeaturePermissionDescription() {
        if (flagsmith.hasFeature('update_feature_state_permission')) {
            return 'Update Feature State';
        }
        return 'Admin';
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
            multivariate_options: projectFlag.multivariate_options.map((v)=>{
                const matching = multivariate_options && multivariate_options.find((m)=>v.id === m.multivariate_feature_option)
                return {
                    ...v,
                    default_percentage_allocation: matching? matching.percentage_allocation : v.default_percentage_allocation
                }
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


        if (str == 'true') {
            if (boolToString) return 'true';
            return true;
        }
        if (str == 'false') {
            if (boolToString) return 'false';
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

    getPlansPermission: (permission) => {
        const isOrgPermission = permission !== '2FA';
        const plans = isOrgPermission? [AccountStore.getActiveOrgPlan()]: AccountStore.getPlans()

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
        if (!plan) {
            return false;
        }
        const date = AccountStore.getDate();
        const cutOff = moment('03-11-20', 'DD-MM-YY');
        if (date && moment(date)
            .valueOf() < cutOff.valueOf()) {
            return true;
        }
        const isSideProjectOrGreater = !plan.includes('side-project');
        const isScaleupOrGreater = !plan.includes('side-project') && !plan.includes('startup');
        switch (permission) {
            case 'FLAG_OWNERS': {
                valid = true;
                break;
            }
            case '2FA': {
                valid = isSideProjectOrGreater
                break;
            }
            case 'RBAC': {
                valid = isSideProjectOrGreater
                break;
            }
            case 'AUDIT': {
                valid = isScaleupOrGreater
                break;
            }
            case 'FORCE_2FA': {
                valid = isScaleupOrGreater
                break;
            }
            case '4_EYES': {
                valid = isScaleupOrGreater
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
            case 'startup-annual-v2':
                return 'Startup';
            case 'scale-up':
            case 'scale-up-annual':
            case 'scale-up-v2':
            case 'scale-up-annual-v2':
                return 'Scale-Up';
            case 'enterprise':
            case 'enterprise-annual':
                return 'Enterprise';
            default:
                return 'Free';
        }
    },
});
