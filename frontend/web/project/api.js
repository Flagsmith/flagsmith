import * as amplitude from '@amplitude/analytics-browser'
import data from 'common/data/base/_data'
import isFreeEmailDomain from 'common/utils/isFreeEmailDomain'

import { loadReoScript } from 'reodotdev'
import { groupBy } from 'lodash'
import getUserDisplayName from 'common/utils/getUserDisplayName'

global.API = {
  ajaxHandler(store, res) {
    switch (res.status) {
      case 404:
        // ErrorModal(null, 'API Not found: ');
        break
      case 503:
        // ErrorModal(null, error);
        break
      default:
      // ErrorModal(null, error);
    }

    // Catch coding errors that end up here
    if (typeof res === 'string') {
      store.error = new Error(res)
      store.goneABitWest()
      return
    }
    if (res instanceof Error) {
      console.error(res)
      store.error = res
      store.goneABitWest()
      return
    } else if (res.data) {
      store.error = res.data
      store.goneABitWest()
      return
    } else if (typeof res.text !== 'function') {
      store.error = res
      store.goneABitWest()
      return
    }

    res
      .text()
      .then((error) => {
        if (store) {
          let err = error
          try {
            err = JSON.parse(error)
          } catch (e) {}
          store.error = err
          store.goneABitWest()
        }
      })
      .catch(() => {
        if (store) {
          store.goneABitWest()
        }
      })
  },
  alias(id, user = {}) {
    if (Project.excludeAnalytics?.includes(id)) return
    Utils.setupCrisp()
    if (Project.reo) {
      const reoPromise = loadReoScript({ clientID: Project.reo })
      reoPromise.then((Reo) => {
        Reo.init({ clientID: Project.reo })
        let authType = 'userID'
        switch (user.auth_type) {
          case 'EMAIL':
            authType = 'email'
            break
          case 'GITHUB':
            authType = 'github'
            break
          case 'GOOGLE':
            authType = 'gmail'
            break
          default:
            break
        }
        const identity = {
          company: user.organisations[0]?.name || '',
          firstname: user.last_name,
          lastname: user.first_name,
          type: authType,
          username: user.email,
        }
        Reo.identify(identity)
      })
    }
    if (Project.amplitude) {
      amplitude.setUserId(id)
      API.trackTraits({
        email: id,
      })
      if (typeof window.engagement !== 'undefined') {
        window.engagement.boot({
          integrations: [
            {
              track: (event) => {
                amplitude.track(event.event_type, event.event_properties)
              },
            },
          ],
          user: {
            user_id: id,
            user_properties: {},
          },
        })
      }
    }
    API.flagsmithIdentify()
  },
  flagsmithIdentify() {
    const user = AccountStore.model
    if (!user) {
      return
    }

    flagsmith
      .identify(user.id, {
        email: user.email,
        organisations: user.organisations
          ? user.organisations.map((o) => `"${o.id}"`).join(',')
          : '',
      })
      .then(() => {
        return flagsmith.setTrait(
          'logins',
          (flagsmith.getTrait('logins') || 0) + 1,
        )
      })
      .then(() => {
        const organisation = AccountStore.getOrganisation()
        const emailDomain = `${user?.email}`?.split('@')[1] || ''
        const freeDomain = isFreeEmailDomain(emailDomain)
        if (
          !freeDomain &&
          typeof delighted !== 'undefined' &&
          flagsmith.hasFeature('delighted')
        ) {
          delighted.survey({
            createdAt: user.date_joined || new Date().toISOString(),
            email: user.email,
            name: `${getUserDisplayName(user)}`, // time subscribed (optional)
            properties: {
              company: organisation?.name,
            },
          })
        }
      })
  },
  getCookie(key) {
    const res = require('js-cookie').get(key)
    if (res) {
      //reset expiry
      API.setCookie(key, res)
    }
    return res
  },
  getEvent() {
    return API.getCookie('event')
  },
  getInvite() {
    return require('js-cookie').get('invite')
  },
  getInviteType() {
    return require('js-cookie').get('invite-type') || 'NO_INVITE'
  },
  getRedirect() {
    return API.getCookie('redirect')
  },
  getReferrer() {
    const r = require('js-cookie').get('r')
    try {
      return JSON.parse(r)
    } catch (e) {
      return null
    }
  },
  identify(id, user = {}) {
    if (Project.excludeAnalytics?.includes(id)) return
    try {
      const planNames = {
        enterprise: 'Enterprise',
        free: 'Free',
        scaleUp: 'Scale-Up',
        startup: 'Startup',
      }

      // Todo: this duplicates functionality in utils.tsx however it would create a circular dependency at the moment
      // we should split out these into a standalone file
      const getPlanName = (plan) => {
        if (plan && plan.includes('free')) {
          return planNames.free
        }
        if (plan && plan.includes('scale-up')) {
          return planNames.scaleUp
        }
        if (plan && plan.includes('startup')) {
          return planNames.startup
        }
        if (plan && plan.includes('start-up')) {
          return planNames.startup
        }
        if (
          global.flagsmithVersion?.backend.is_enterprise ||
          (plan && plan.includes('enterprise'))
        ) {
          return planNames.enterprise
        }
        return planNames.free
      }

      const orgsByPlan = groupBy(AccountStore.getOrganisations(), (org) =>
        getPlanName(org?.subscription?.plan),
      )
      //Picks the organisation with the highest plan
      const selectedOrg =
        orgsByPlan?.[planNames.enterprise]?.[0] ||
        orgsByPlan?.[planNames.scaleUp]?.[0] ||
        orgsByPlan?.[planNames.startup]?.[0] ||
        orgsByPlan?.[planNames.free]?.[0]
      const selectedPlanName = Utils.getPlanName(
        selectedOrg?.subscription?.plan,
      )
      const selectedRole = selectedOrg?.role //ADMIN | USER
      const selectedOrgName = selectedOrg?.name

      API.trackTraits({
        email: id,
        integrations: user.onboarding?.tools?.integrations || [],
        name: { 'first': user.first_name, 'last': user.last_name },
        organisation: selectedOrgName,
        plan: selectedPlanName,
        role: selectedRole,
        tasks: (user.onboarding?.tasks || [])?.map((v) => v.name),
      })
      API.flagsmithIdentify()
    } catch (e) {
      console.error('Error identifying', e)
    }
  },
  log() {
    console.log.apply(this, arguments)
  },
  postEvent(event, tag) {
    if (!AccountStore.getUser()) return
    const organisation = AccountStore.getOrganisation()
    const name =
      organisation && organisation.name ? ` - ${organisation.name}` : ''
    return data.post('/api/event', {
      event: `${event}(${AccountStore.getUser().email} ${
        AccountStore.getUser().first_name
      } ${AccountStore.getUser().last_name})${name}`,
      tag,
    })
  },
  reset() {
    return flagsmith.logout()
  },
  setCookie(key, v) {
    try {
      if (!v) {
        require('js-cookie').remove(key, {
          domain: Project.cookieDomain,
          path: '/',
        })
        require('js-cookie').remove(key, { path: '/' })
      } else {
        if (E2E) {
          // Since E2E is not https, we can't set secure cookies
          require('js-cookie').set(key, v, { expires: 30, path: '/' })
        } else {
          // We need samesite secure cookies to allow for IFrame embeds from 3rd parties
          require('js-cookie').set(key, v, {
            expires: 30,
            path: '/',
            sameSite: Project.cookieSameSite || 'none',
            secure: Project.useSecureCookies,
          })
        }
      }
    } catch (e) {}
  },
  setEvent(v) {
    return API.setCookie('event', v)
  },
  setInvite(id) {
    const cookie = require('js-cookie')
    cookie.set('invite', id)
  },
  setInviteType(id) {
    const cookie = require('js-cookie')
    cookie.set('invite-type', id)
  },
  setRedirect(v) {
    return API.setCookie('redirect', v)
  },
  trackEvent(data) {
    if (Project.ga) {
      if (Project.logAnalytics) {
        console.log('ANALYTICS EVENT', data)
      }
      if (!data) {
        console.error('Passed null event data')
      }
      console.info('track', data)
      if (!data || !data.category || !data.event) {
        console.error('Invalid event provided', data)
      }
      if (data.category === 'First') {
        API.postEvent(
          data.event + (data.extra ? ` ${data.extra}` : ''),
          'first_events',
        )
      }
      ga('send', {
        eventAction: data.event,
        eventCategory: data.category,
        eventLabel: data.label,
        hitType: 'event',
      })
    }

    if (Project.amplitude) {
      const eventData = {
        category: data.category,
        ...(data.extra || {}),
      }

      amplitude.track(data.event, eventData)
    }
  },
  trackPage(title) {
    if (Project.ga) {
      ga('send', {
        hitType: 'pageview',
        location: document.location.href,
        page: document.location.pathname,
        title,
      })
    }
  },
  trackTraits(traits) {
    if (Project.amplitude && traits) {
      const identifyObj = new amplitude.Identify()
      for (const [key, value] of Object.entries(traits)) {
        identifyObj.set(key, value)
      }
      amplitude.identify(identifyObj)
    }
  },
}

export default API
