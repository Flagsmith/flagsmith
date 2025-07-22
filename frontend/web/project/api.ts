// @ts-ignore
import data from 'common/data/base/_data'
// @ts-ignore
import { loadReoScript, ReoInstance } from 'reodotdev'
import * as amplitude from '@amplitude/analytics-browser'
import isFreeEmailDomain from 'common/utils/isFreeEmailDomain'
import { groupBy } from 'lodash'
import getUserDisplayName from 'common/utils/getUserDisplayName'
const Cookies = require('js-cookie')
import Project from 'common/project'
import { AccountModel, User } from 'common/types/responses'
import AccountStore from 'common/stores/account-store'
import flagsmith from 'flagsmith'
import Utils from 'common/utils/utils'

const API = {
  ajaxHandler(
    store: { error?: any; goneABitWest: () => void },
    res: string | Error | { data?: any; text?: () => Promise<string> },
  ): void {
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
    }
    if (res.data) {
      store.error = res.data
      store.goneABitWest()
      return
    }
    if (typeof (res as any).text !== 'function') {
      store.error = res
      store.goneABitWest()
      return
    }

    ;(res as any)
      .text()
      .then((errorText: string) => {
        let err: any = errorText
        try {
          err = JSON.parse(errorText)
        } catch {}
        store.error = err
        store.goneABitWest()
      })
      .catch(() => {
        if (store) {
          store.goneABitWest()
        }
      })
  },

  alias(id: string, user: Partial<AccountModel> = {}): void {
    if (Project.excludeAnalytics?.includes(id)) return

    Utils.setupCrisp()
    if (Project.reo) {
      loadReoScript({ clientID: Project.reo }).then(
        (Reo: typeof ReoInstance) => {
          Reo.init({ clientID: Project.reo! })
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
          Reo.identify({
            company: user.organisations?.[0]?.name || '',
            firstname: user.last_name ?? '',
            lastname: user.first_name ?? '',
            type: authType,
            username: user.email ?? '',
          })
        },
      )
    }

    if (Project.amplitude) {
      amplitude.setUserId(id)
      API.trackTraits({ email: id })
      if (window.engagement) {
        window.engagement.boot({
          integrations: [
            {
              track: (event: any) =>
                amplitude.track(event.event_type, event.event_properties),
            },
          ],
          user: { user_id: id, user_properties: {} },
        })
      }
    }
    API.flagsmithIdentify()
  },

  flagsmithIdentify(): void {
    //@ts-ignore
    const user = AccountStore.model as unknown as AccountModel
    if (!user) return

    flagsmith
      .identify(`${user.id}`, {
        email: user.email,
        organisations: user.organisations
          ? user.organisations.map((o) => String(o.id)).join(',')
          : '',
      })
      .then(() =>
        flagsmith.setTrait(
          'logins',
          ((flagsmith.getTrait('logins') as number) || 0) + 1,
        ),
      )
      .then(() => {
        const organisation = AccountStore.getOrganisation()
        const emailDomain = user.email.split('@')[1] || ''
        const freeDomain = isFreeEmailDomain(emailDomain)
        if (
          !freeDomain &&
          typeof delighted !== 'undefined' &&
          flagsmith.hasFeature('delighted')
        ) {
          delighted.survey({
            createdAt: user.date_joined || new Date().toISOString(),
            email: user.email,
            name: getUserDisplayName(user),
            properties: { company: organisation?.name },
          })
        }
      })
  },

  getCookie(key: string): string | undefined {
    const val = Cookies.get(key)
    if (val) API.setCookie(key, val)
    return val
  },

  getEvent(): string | undefined {
    return API.getCookie('event')
  },

  getInvite(): string | undefined {
    return Cookies.get('invite')
  },

  getInviteType(): string {
    return Cookies.get('invite-type') || 'NO_INVITE'
  },

  getRedirect(): string | undefined {
    return API.getCookie('redirect')
  },

  getReferrer(): any {
    const r = Cookies.get('r')
    try {
      return JSON.parse(r!)
    } catch {
      return null
    }
  },

  identify(id: string | number, user: Partial<User> = {}): void {
    if (Project.excludeAnalytics?.includes(String(id))) return
    try {
      const planNames = {
        enterprise: 'Enterprise',
        free: 'Free',
        scaleUp: 'Scale-Up',
        startup: 'Startup',
      }
      const getPlanName = (plan?: string): string => {
        if (!plan) return planNames.free
        if (plan.includes('free')) return planNames.free
        if (plan.includes('scale-up')) return planNames.scaleUp
        if (plan.includes('startup') || plan.includes('start-up'))
          return planNames.startup
        if (Project.backend?.is_enterprise || plan.includes('enterprise'))
          return planNames.enterprise
        return planNames.free
      }

      const orgsByPlan = groupBy(AccountStore.getOrganisations(), (org) =>
        getPlanName(org.subscription?.plan || ''),
      )
      const selectedOrg =
        orgsByPlan.Enterprise?.[0] ||
        orgsByPlan['Scale-Up']?.[0] ||
        orgsByPlan.Startup?.[0] ||
        orgsByPlan.Free?.[0]
      const selectedPlanName = Utils.getPlanName?.(
        selectedOrg?.subscription?.plan || '',
      )
      const selectedRole = selectedOrg?.role
      const selectedOrgName = selectedOrg?.name

      API.trackTraits({
        email: String(id),
        integrations: user.onboarding?.tools?.integrations || [],
        name: { first: user.first_name, last: user.last_name },
        organisation: selectedOrgName,
        plan: selectedPlanName,
        role: selectedRole,
        tasks: user.onboarding?.tasks?.map((t) => t.name) || [],
      })
      API.flagsmithIdentify()
    } catch (err) {
      console.error('Error identifying', err)
    }
  },

  log(...args: any[]): void {
    console.log(...args)
  },

  postEvent(event: string, tag?: string): Promise<any> | void {
    const currentUser = AccountStore.getUser()
    if (!currentUser) return
    const organisation = AccountStore.getOrganisation()
    const name = organisation?.name ? ` - ${organisation.name}` : ''
    return data.post('/api/event', {
      event: `${event}(${currentUser.email} ${currentUser.first_name} ${currentUser.last_name})${name}`,
      tag,
    })
  },

  reset(): Promise<any> {
    return flagsmith.logout()
  },

  setCookie(key: string, v?: string): void {
    if (!v) {
      Cookies.remove(key, { domain: Project.cookieDomain, path: '/' })
      Cookies.remove(key, { path: '/' })
    } else {
      const opts = { expires: 30, path: '/' }
      if (!E2E)
        Object.assign(opts, {
          sameSite: Project.cookieSameSite || 'none',
          secure: Project.useSecureCookies,
        })
      Cookies.set(key, v, opts)
    }
  },

  setEvent(v: string): void {
    API.setCookie('event', v)
  },

  setInvite(id: string): void {
    Cookies.set('invite', id)
  },

  setInviteType(id: string): void {
    Cookies.set('invite-type', id)
  },

  setRedirect(v: string): void {
    API.setCookie('redirect', v)
  },

  trackEvent(data: {
    category: string
    event: string
    label?: string
    extra?: Record<string, any>
  }): void {
    if (Project.ga) {
      if (Project.logAnalytics) console.log('ANALYTICS EVENT', data)
      if (!data || !data.category || !data.event)
        return console.error('Invalid event provided', data)
      if (data.category === 'First')
        API.postEvent(
          `${data.event}${data.extra ? ` ${JSON.stringify(data.extra)}` : ''}`,
          'first_events',
        )
      ga('send', {
        eventAction: data.event,
        eventCategory: data.category,
        eventLabel: data.label,
        hitType: 'event',
      })
    }
    if (Project.amplitude) {
      amplitude.track(data.event, {
        category: data.category,
        ...(data.extra || {}),
      })
    }
  },

  trackPage(title: string): void {
    if (Project.ga)
      ga('send', {
        hitType: 'pageview',
        location: document.location.href,
        page: document.location.pathname,
        title,
      })
  },

  trackTraits(traits: Record<string, any>): void {
    if (Project.amplitude && traits) {
      const identifyObj = new amplitude.Identify()
      Object.entries(traits).forEach(([key, value]) =>
        identifyObj.set(key, value),
      )
      amplitude.identify(identifyObj)
    }
  },
}
//@ts-ignore //todo: remove global usages / circular dependencies of API
global.API = API
export default API
