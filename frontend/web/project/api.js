import amplitude from 'amplitude-js';
import data from '../../common/data/base/_data';

global.API = {
    ajaxHandler(store, res) {
        switch (res.status) {
            case 404:
                // ErrorModal(null, 'API Not found: ');
                break;
            case 503:
                // ErrorModal(null, error);
                break;
            default:
      // ErrorModal(null, error);
        }

        // Catch coding errors that end up here
        if (res instanceof Error) {
            console.log(res);
            return;
        }

        res.text().then((error) => {
            if (store) {
                let err = error;
                try {
                    err = JSON.parse(error);
                } catch (e) {}
                store.error = err;
                store.goneABitWest();
            }
        }).catch((e) => {
            if (store) {
                store.goneABitWest();
            }
        });
    },
    trackEvent(data) {
        if (Project.ga) {
            if (Project.logAnalytics) {
                console.log('ANALYTICS EVENT', data);
            }
            if (!data) {
                console.error('Passed null event data');
            }
            console.info('track', data);
            if (!data || !data.category || !data.event) {
                console.error('Invalid event provided', data);
            }
            if (data.category === 'First') {
                API.postEvent(data.event + (data.extra ? ` ${data.extra}` : ''), 'first_events');
            }
            ga('send', {
                hitType: 'event',
                eventCategory: data.category,
                eventAction: data.event,
                eventLabel: data.label,
            });
        }

        if (Project.mixpanel) {
            if (!data) {
                console.error('Passed null event data');
            }
            console.info('track', data);
            if (!data || !data.category || !data.event) {
                console.error('Invalid event provided', data);
            }
            mixpanel.track(data.event, {
                category: data.category,
            });
        }
    },
    postEvent(event, tag) {
        if (!AccountStore.getUser()) return;
        const organisation = AccountStore.getOrganisation();
        const name = organisation && organisation.name ? ` - ${organisation.name}` : '';
        return data.post('/api/event', { tag, event: `${event}(${AccountStore.getUser().email} ${AccountStore.getUser().first_name} ${AccountStore.getUser().last_name})${name}` });
    },
    getReferrer() {
        const r = require('js-cookie').get('r');
        try {
            return JSON.parse(r);
        } catch (e) {
            return null;
        }
    },
    getEvent() {
        return API.getCookie('event');
    },
    setEvent(v) {
        return API.setCookie('event', v);
    },
    getCookie(key) {
        return require('js-cookie').get(key);
    },
    setCookie(key, v) {
        try {
            require('js-cookie').set(key, v, { path: '/' });
            require('js-cookie').set(key, v, { path: '/', domain: Project.cookieDomain });
        } catch (e) {

        }
    },
    setInvite(id) {
        const cookie = require('js-cookie');
        cookie.set('invite', id);
    },
    getInvite() {
        return require('js-cookie').get('invite');
    },
    trackPage(title) {
        if (Project.ga) {
            ga('send', {
                hitType: 'pageview',
                title,
                location: document.location.href,
                page: document.location.pathname,
            });
        }

        if (Project.mixpanel) {
            mixpanel.track(`Page View  - ${title}`, {
                title,
                location: document.location.href,
                page: document.location.pathname,
            });
        }
    },
    alias(id) {
        if (id === Project.excludeAnalytics) return;
        if (Project.mixpanel) {
            mixpanel.alias(id);
        }

        if (Project.amplitude) {
            amplitude.getInstance().setUserId(id);
            const identify = new amplitude.Identify()
                .set('email', id);
            amplitude.getInstance().identify(identify);
        }
        flagsmith.identify(id);
        flagsmith.setTrait('email', id);
    },
    identify(id, user = {}) {
        if (id === Project.excludeAnalytics) return;
        try {
            const orgs = (user && user.organisations && _.map(user.organisations, o => `${o.name} #${o.id}(${o.role})[${o.num_seats}]`).join(',')) || '';
            if (Project.mixpanel) {
                mixpanel.identify(id);
                const plans = AccountStore.getPlans();

                mixpanel.people.set({
                    '$email': id, // only reserved properties need the $
                    'USER_ID': id, // use human-readable names
                    '$first_name': user.first_name,
                    'isCompanyEmail': !user.email.includes('@gmail') && !user.email.includes('@yahoo') && !user.email.includes('@hotmail') && !user.email.includes('@icloud'),
                    '$last_name': user.last_name,
                    'plan': plans && plans.join(','),
                    orgs,
                });
            }

            if (Project.amplitude) {
                amplitude.getInstance().setUserId(id);
                const identify = new amplitude.Identify()
                    .set('email', id)
                    .set('name', { 'first': user.first_name, 'last': user.last_name });

                amplitude.getInstance().identify(identify);
            }
            flagsmith.identify(id);
            flagsmith.setTrait('organisations', user.organisations ? user.organisations.map(o => `"${o.id}"`).join(',') : '');
            flagsmith.setTrait('email', id);
            if (window.$crisp) {
                $crisp.push(['set', 'user:email', id]);
                $crisp.push(['set', 'user:nickname', `${user.first_name} ${user.last_name}`]);
                if (orgs) {
                    $crisp.push(['set', 'user:company', orgs]);
                }
            }
        } catch (e) {
            console.error('Error identifying', e);
        }
    },
    register(email, firstName, lastName) {
        if (email === Project.excludeAnalytics) return;
        if (Project.mixpanel) {
            mixpanel.register({
                'Email': email,
                'First Name': firstName,
                'Last Name': lastName,
            });
        }
    },
    reset() {
        if (Project.mixpanel) {
            mixpanel.reset();
        }
        flagsmith.logout();
    },
    log() {
        console.log.apply(this, arguments);
    },
};
