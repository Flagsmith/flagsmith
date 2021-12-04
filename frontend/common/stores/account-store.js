import OrganisationStore from './organisation-store';
import ConfigStore from './config-store';

const BaseStore = require('./base/_store');
const data = require('../data/base/_data');

const controller = {
    register: ({ email, password, first_name, last_name, organisation_name = 'Default Organisation' }, isInvite) => {
        store.saving();
        data.post(`${Project.api}auth/users/`, {
            email,
            password,
            first_name,
            last_name,
            referrer: API.getReferrer() || '',
        })
            .then((res) => {
                data.setToken(res.key);
                API.trackEvent(Constants.events.REGISTER);
                if (API.getReferrer()) {
                    API.trackEvent(Constants.events.REFERRER_REGISTERED(API.getReferrer().utm_source));
                }

                store.isSaving = false;
                return controller.onLogin();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
    oauth: (type, _data) => {
        store.loading();
        API.trackEvent(Constants.events.OAUTH(type));

        data.post(type === 'saml' ? `${Project.api}auth/saml/login/` : `${Project.api}auth/oauth/${type}/`, _data)
            .then((res) => {
                // const isDemo = email == Project.demoAccount.email;
                // store.isDemo = isDemo;
                // if (isDemo) {
                //     AsyncStorage.setItem('isDemo', `${isDemo}`);
                //     API.trackEvent(Constants.events.LOGIN_DEMO);
                // } else {
                //     API.trackEvent(Constants.events.LOGIN);
                //     API.identify(email);
                // }
                if (res.ephemeral_token) {
                    store.ephemeral_token = res.ephemeral_token;
                    store.model = {
                        twoFactorPrompt: true,
                        twoFactorEnabled: true,
                    };
                    store.loaded();
                    return;
                }

                data.setToken(res.key);
                return controller.onLogin();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
    resetPassword: (uid, token, new_password1, new_password2) => {
        store.saving();
        data.post(`${Project.api}auth/users/reset_password_confirm/`, {
        // data.post(`${Project.api}auth/password/reset/confirm/`, {
            uid,
            token,
            new_password: new_password1,
            re_new_password: new_password2,
        })
            .then((res) => {
                store.saved();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
    setToken: (token) => {
        store.loading();
        store.user = {};
        AsyncStorage.getItem('isDemo', (err, res) => {
            if (res) {
                store.isDemo = true;
            }
            data.setToken(token);
            return controller.onLogin();
        });
    },
    login: ({ email, password }) => {
        store.loading();
        data.post(`${Project.api}auth/login/`, {
            email,
            password,
        })
            .then((res) => {
                const isDemo = email == Project.demoAccount.email;
                store.isDemo = isDemo;
                if (isDemo) {
                    AsyncStorage.setItem('isDemo', `${isDemo}`);
                    API.trackEvent(Constants.events.LOGIN_DEMO);
                } else {
                    API.trackEvent(Constants.events.LOGIN);
                }
                if (res.ephemeral_token) {
                    store.ephemeral_token = res.ephemeral_token;
                    store.model = {
                        twoFactorPrompt: true,
                        twoFactorEnabled: true,
                    };
                    store.loaded();
                    return;
                }

                data.setToken(res.key);
                return controller.onLogin();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
    onLogin: (skipCaching) => {
        if (!skipCaching) {
            API.setCookie('t', data.token);
        }
        return controller.getOrganisations();
    },
    acceptInvite: (id) => {
        store.saving();
        API.setInvite('');
        return data.post(`${Project.api}users/join/link/${id}/`)
            .catch(() => data.post(`${Project.api}users/join/${id}/`))
            .then((res) => {
                store.savedId = res.id;
                store.model.organisations.push(res);
                const ev = Constants.events.ACCEPT_INVITE(res.name);
                API.postEvent(ev.event + (ev.extra ? ` ${ev.extra}` : ''), 'first_events')
                    .catch(() => {})
                    .finally(() => {
                        AsyncStorage.setItem('user', JSON.stringify(store.model));
                        store.saved();
                    });
            })
            .catch((e) => {
                API.ajaxHandler(store, e);
            });
    },
    enableTwoFactor: () => {
        store.saving();
        return data.post(`${Project.api}auth/app/activate/`)
            .then((res) => {
                store.model.twoFactor = res;
                store.model.twoFactorEnabled = true;
                store.saved();
            });
    },
    twoFactorLogin: (pin, onError) => {
        store.saving();
        return data.post(`${Project.api}auth/login/code/`, { code: pin, ephemeral_token: store.ephemeral_token })
            .then((res) => {
                store.model = null;
                API.trackEvent(Constants.events.LOGIN);
                data.setToken(res.key);
                store.ephemeral_token = null;
                controller.onLogin();
            }).catch((e) => {
                if (onError) {
                    onError();
                }
                API.ajaxHandler(store, e);
            });
    },
    disableTwoFactor: () => {
        store.saving();
        return data.post(`${Project.api}auth/app/deactivate/`)
            .then(() => {
                store.model.twoFactorEnabled = false;
                store.model.twoFactorConfirmed = false;
                store.saved();
            });
    },
    confirmTwoFactor: (pin, onError) => {
        store.saving();

        return data.post(`${Project.api}auth/app/activate/confirm/`, { code: pin })
            .then((res) => {
                store.model.backupCodes = res.backup_codes;
                store.model.twoFactorEnabled = true;
                store.model.twoFactorConfirmed = true;

                store.saved();
            }).catch((e) => {
                if (onError) {
                    onError();
                }
                API.ajaxHandler(store, e);
            });
    },
    getOrganisations: () => Promise.all([data.get(`${Project.api}organisations/`), data.get(`${Project.api}auth/users/me/`), data.get(`${Project.api}auth/mfa/user-active-methods/`)])
        .then(([res, userRes, methods]) => {
            controller.setUser({
                ...userRes,
                twoFactorEnabled: !!methods.length,
                twoFactorConfirmed: !!methods.length,
                twoFactorPrompt: store.ephemeral_token && !!methods.length,
                organisations: res.results,
            });
        })
        .catch(e => API.ajaxHandler(store, e)),

    selectOrganisation: (id) => {
        store.organisation = _.find(store.model.organisations, { id });
        store.changed();
    },

    editOrganisation: (org) => {
        API.trackEvent(Constants.events.EDIT_ORGANISATION);
        data.put(`${Project.api}organisations/${store.organisation.id}/`, org)
            .then((res) => {
                const idx = _.findIndex(store.model.organisations, { id: store.organisation.id });
                if (idx != -1) {
                    store.model.organisations[idx] = res;
                    store.organisation = res;
                }
                store.saved();
            });
    },

    createOrganisation: (name) => {
        store.saving();
        if (!AccountStore.model.organisations || !AccountStore.model.organisations.length) {
            API.trackEvent(Constants.events.CREATE_FIRST_ORGANISATION);
        }
        API.trackEvent(Constants.events.CREATE_ORGANISATION);
        if (API.getReferrer()) {
            // eslint-disable-next-line camelcase
            API.postEvent(`New Organisation ${name} from ${`${API.getReferrer().utm_source}`}`);
            API.trackEvent(Constants.events.REFERRER_CONVERSION(API.getReferrer().utm_source));
        } else {
            // eslint-disable-next-line camelcase
            API.postEvent(`New Organisation ${name}`);
        }
        data.post(`${Project.api}organisations/`, { name })
            .then((res) => {
                store.model.organisations = store.model.organisations.concat([{ ...res, role: 'ADMIN' }]);
                AsyncStorage.setItem('user', JSON.stringify(store.model));
                store.savedId = res.id;
                store.saved();
            });
    },

    setUser(user) {
        if (user) {
            store.model = user;
            store.organisation = user && user.organisations && user.organisations[0];


            if (projectOverrides.delighted) {
                delighted.survey({
                    email: store.model.email, // customer email (optional)
                    name: `${store.model.first_name} ${store.model.last_name}`, // customer name (optional)
                    createdAt: store.organisation && store.organisation.created_date, // time subscribed (optional)
                    properties: { // extra context (optional)
                        company: store.organisation && store.organisation.name,
                    },
                });
            }

            AsyncStorage.setItem('user', JSON.stringify(store.model));
            if (!store.isDemo) {
                API.alias(user.email);
                API.identify(user && user.email, user);
            }
            store.loaded();
        } else if (!user) {
            store.ephemeral_token = null;
            AsyncStorage.clear();
            API.setCookie('t', '');
            data.setToken(null);
            store.isDemo = false;
            store.model = user;
            store.organisation = null;
            store.trigger('logout');
            API.reset();
        }
    },

    deleteOrganisation: () => {
        API.trackEvent(Constants.events.DELETE_ORGANISATION);
        data.delete(`${Project.api}organisations/${store.organisation.id}/`)
            .then((res) => {
                store.model.organisations = _.filter(store.model.organisations, org => org.id !== store.organisation.id);
                store.organisation = store.model.organisations.length ? store.model.organisations[0] : null;
                store.trigger('removed');
                AsyncStorage.setItem('user', JSON.stringify(store.model));
            });
    },

    updateSubscription: (hostedPageId) => {
        data.post(`${Project.api}organisations/${store.organisation.id}/update-subscription/`, { hosted_page_id: hostedPageId })
            .then((res) => {
                const idx = _.findIndex(store.model.organisations, { id: store.organisation.id });
                if (idx !== -1) {
                    store.model.organisations[idx] = res;
                    try {
                        if (res && res.subscription && res.subscription.plan) {
                            API.postEvent(res.subscription.plan, 'chargebee');
                        }
                    } catch (e) {}
                    store.organisation = res;
                }
                store.saved();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
};


const store = Object.assign({}, BaseStore, {
    id: 'account',
    getUser() {
        return store.model;
    },
    setToken(token) {
        data.token = token;
    },
    getUserId() {
        return store.model && store.model.id;
    },
    forced2Factor() {
        if (!store.model || !store.model.organisations) return false;

        if (store.model.twoFactorConfirmed) {
            return false;
        }

        return flagsmith.hasFeature('forced_2fa') && store.getOrganisations() && store.getOrganisations().find(o => o.force_2fa);
    },
    setUser(user) {
        controller.setUser(user);
    },
    getOrganisation() {
        return store.organisation;
    },
    getOrganisationPlan(id) {
        const organisations = store.getOrganisations();
        const organisation = organisations && organisations.find(v => v.id === id);
        if (organisation) {
            return !!organisation.subscription;
        }
        return null;
    },
    isAdmin() {
        const id = store.organisation && store.organisation.id;
        return id && store.getOrganisationRole(id) === 'ADMIN';
    },
    getPlans() {
        return _.filter(store.model.organisations.map(org => org.subscription && org.subscription.plan), plan => !!plan);
    },
    getDate() {
        return store.getOrganisation() && store.getOrganisation().created_date;
    },
    getOrganisations() {
        return store.model && store.model.organisations;
    },
    getOrganisationRole(id) {
        return store.model && store.model.organisations && _.get(_.find(store.model.organisations, org => (id ? org.id === id : org.id === (store.organisation && store.organisation.id))), 'role');
    },
});

store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction

    switch (action.actionType) {
        case Actions.SET_USER:
            controller.setUser(action.user);
            break;
        case Actions.SET_TOKEN:
            controller.setToken(action.token);
            break;
        case Actions.SELECT_ORGANISATION:
            controller.selectOrganisation(action.id);
            break;
        case Actions.CREATE_ORGANISATION:
            controller.createOrganisation(action.name);
            break;
        case Actions.ACCEPT_INVITE:
            controller.acceptInvite(action.id);
            break;
        case Actions.DELETE_ORGANISATION:
            controller.deleteOrganisation();
            break;
        case Actions.EDIT_ORGANISATION:
            controller.editOrganisation(action.org);
            break;
        case Actions.LOGOUT:
            controller.setUser(null);
            break;
        case Actions.REGISTER:
            controller.register(action.details, action.isInvite);
            break;
        case Actions.RESET_PASSWORD:
            controller.resetPassword(action.uid, action.token, action.new_password1, action.new_password2);
            break;
        case Actions.LOGIN:
            controller.login(action.details);
            break;
        case Actions.GET_ORGANISATIONS:
            controller.getOrganisations();
            break;
        case Actions.ENABLE_TWO_FACTOR:
            controller.enableTwoFactor();
            break;
        case Actions.CONFIRM_TWO_FACTOR:
            controller.confirmTwoFactor(action.pin, action.onError);
            break;
        case Actions.DISABLE_TWO_FACTOR:
            controller.disableTwoFactor();
            break;
        case Actions.OAUTH:
            controller.oauth(action.oauthType, action.data);
            break;
        case Actions.TWO_FACTOR_LOGIN:
            controller.twoFactorLogin(action.pin, action.onError);
            break;
        case Actions.UPDATE_SUBSCRIPTION:
            controller.updateSubscription(action.hostedPageId);
            break;
        default:
    }
});

controller.store = store;
module.exports = controller.store;
