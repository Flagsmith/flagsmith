import flagsmith from 'flagsmith'
import moment from 'moment'
import AccountStore from './stores/account-store'
import { getStore } from './store'
import { selectBuildVersion } from './services/useBuildVersion'
import getUserDisplayName from './utils/getUserDisplayName'
import { AccountModel, Organisation } from './types/responses'
import Project from './project'

// Used in self-hosted pages where users can opt into reaching out
const defaultCrispID = '8857f89e-0eb5-4263-ab49-a293872b6c19'
const defaultPylonID = '028babb7-d93f-4e32-be6a-59db190a084f'

async function loadCrisp(crispWebsiteId: string) {
  // @ts-ignore
  if (window.$crisp) {
    return
  }
  // @ts-ignore
  window.$crisp = []
  // @ts-ignore
  window.CRISP_WEBSITE_ID = crispWebsiteId
  await new Promise((resolve, reject) => {
    const d = document
    const s = d.createElement('script')
    s.src = 'https://client.crisp.chat/l.js'
    s.async = true
    s.onload = resolve
    s.onerror = reject
    d.getElementsByTagName('head')[0].appendChild(s)
  })
}

async function loadPylon(pylonAppId: string) {
  // @ts-ignore
  if (window.Pylon) {
    return
  }

  // Initialize Pylon using their recommended script format
  await new Promise((resolve, reject) => {
    const t = document
    const n = function (...args: any[]) {
      // @ts-ignore
      n.q.push(args)
    }
    // @ts-ignore
    n.q = []
    // @ts-ignore
    window.Pylon = n

    const s = t.createElement('script')
    s.setAttribute('type', 'text/javascript')
    s.setAttribute('async', 'true')
    s.setAttribute('src', `https://widget.usepylon.com/widget/${pylonAppId}`)
    s.onload = () => resolve(undefined)
    s.onerror = reject
    const firstScript = t.getElementsByTagName('script')[0]
    firstScript.parentNode?.insertBefore(s, firstScript)
  })
}

function setupCrisp() {
  const user = AccountStore.model as AccountModel
  if (typeof $crisp === 'undefined' || !user) {
    return
  }
  const isSaas = () =>
    selectBuildVersion(getStore().getState())?.backend?.is_saas
  $crisp.push([
    'set',
    'session:data',
    [[['hosting', isSaas() ? 'SaaS' : 'Self-Hosted']]],
  ])
  const organisation = AccountStore.getOrganisation() as Organisation
  const formatOrganisation = (o: Organisation) => {
    const plan = AccountStore.getActiveOrgPlan()
    return `${o.name} (${plan}) #${o.id}`
  }
  const otherOrgs = user?.organisations.filter((v) => v.id !== organisation?.id)
  if (window.$crisp) {
    $crisp.push(['set', 'user:email', user.email])
    $crisp.push(['set', 'user:nickname', `${getUserDisplayName(user)}`])
    if (otherOrgs.length) {
      $crisp.push([
        'set',
        'session:data',
        [[['other-orgs', `${otherOrgs?.length} other organisations`]]],
      ])
    }
    $crisp.push([
      'set',
      'session:data',
      [
        [
          ['user-id', `${user.id}`],
          ['date-joined', `${moment(user.date_joined).format('Do MMM YYYY')}`],
        ],
      ],
    ])
    if (organisation) {
      $crisp.push(['set', 'user:company', formatOrganisation(organisation)])
      $crisp.push([
        'set',
        'session:data',
        [[['seats', organisation.num_seats]]],
      ])
    }
  }
}

function setupPylon() {
  const user = AccountStore.model as AccountModel
  if (typeof window.Pylon === 'undefined' || !user) {
    return
  }

  try {
    window.pylon = {
      chat_settings: {
        account_id: String(user.id),
        app_id: Project.pylonAppId || defaultPylonID,
        email: user.email,
        email_hash: user.pylon_email_signature,
        name: getUserDisplayName(user),
      },
    }
  } catch (error) {
    console.error('Error setting up Pylon:', error)
  }
}

export function identifyChatUser() {
  const usePylon = flagsmith.hasFeature('pylon_chat')

  if (usePylon) {
    setupPylon()
  } else {
    setupCrisp()
  }
}

export function openChat() {
  const usePylon = flagsmith.hasFeature('pylon_chat')

  if (usePylon && typeof window.Pylon !== 'undefined') {
    window.Pylon('show')
    setupPylon()
  } else if (typeof $crisp !== 'undefined') {
    $crisp.push(['do', 'chat:open'])
    setupCrisp()
  }
}

export default async function loadChat(forceDefaultAPIKey?: boolean) {
  try {
    const isWidget = document.location.href.includes('/widget')
    if (isWidget) return

    const usePylon = flagsmith.hasFeature('pylon_chat')
    const pylonId = forceDefaultAPIKey ? defaultPylonID : Project.pylonAppId
    const crispId = forceDefaultAPIKey ? defaultCrispID : Project.crispChat

    if (usePylon && pylonId) {
      await loadPylon(pylonId)
    } else if (crispId) {
      await loadCrisp(crispId)
    }
  } catch (error) {
    console.error('Failed to initialize chat widget:', error)
  }
}
