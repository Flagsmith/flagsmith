declare global {
  interface Window {
    Pylon?: ((...args: unknown[]) => void) & { q?: unknown[][] }
    pylon?: { chat_settings: Record<string, string | undefined> }
    hsConversationsSettings?: {
      loadImmediately?: boolean
      identificationEmail?: string
      identificationToken?: string
    }
    hsConversationsOnReady?: (() => void)[]
    HubSpotConversations?: {
      widget: {
        load: (options?: { widgetOpen?: boolean }) => void
        open: () => void
        remove: () => void
        status: () => { loaded: boolean }
      }
    }
  }
}

import AccountStore from './stores/account-store'
import data from './data/base/_data'
import getUserDisplayName from './utils/getUserDisplayName'
import Utils from './utils/utils'
import { AccountModel } from './types/responses'
import Project from './project'

const defaultPylonID = '028babb7-d93f-4e32-be6a-59db190a084f'
const SUPPORT_EMAIL_URL = 'mailto:support@flagsmith.com'

export type ChatProvider = 'hubspot' | 'pylon'

// hubspot_chat's value sets who gets HubSpot chat: "all" opens it to every
// plan, anything else (including no value) keeps it to paid plans.
const HUBSPOT_CHAT_ALL_PLANS = 'all'

// HubSpot wins while both flags are on, so turning hubspot_chat on is enough
// to switch provider.
export function getChatProvider(): ChatProvider | null {
  const isFreePlan = Utils.isOrgOnFreePlan()
  if (Utils.getFlagsmithHasFeature('hubspot_chat')) {
    const audience = `${Utils.getFlagsmithValue('hubspot_chat') ?? ''}`
      .trim()
      .toLowerCase()
    return audience === HUBSPOT_CHAT_ALL_PLANS || !isFreePlan ? 'hubspot' : null
  }
  if (Utils.getFlagsmithHasFeature('pylon_chat') && !isFreePlan) return 'pylon'
  return null
}

async function loadPylon(pylonAppId: string) {
  if (window.Pylon) {
    return
  }

  await new Promise((resolve, reject) => {
    const t = document
    const n: ((...args: unknown[]) => void) & { q?: unknown[][] } =
      Object.assign((...args: unknown[]) => n.q!.push(args), { q: [] })
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

function setupPylon() {
  const user = AccountStore.getUser() as AccountModel
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

function hidePylon() {
  if (typeof window.Pylon !== 'undefined') {
    window.Pylon('hideChatBubble')
  }
}

function canLoadHubSpot() {
  const widget = window.HubSpotConversations?.widget
  return !!widget && getChatProvider() === 'hubspot' && !widget.status().loaded
}

// Tells HubSpot who is chatting, so their tickets get a contact instead of
// "Unknown Visitor". HubSpot reads this when load() is called. Without a token
// (an API without the endpoint, or HubSpot failing) the widget still loads,
// just anonymously.
async function identifyHubSpotVisitor() {
  const settings = { ...window.hsConversationsSettings }
  delete settings.identificationEmail
  delete settings.identificationToken
  window.hsConversationsSettings = settings

  const user = AccountStore.getUser() as AccountModel | undefined
  if (!user?.email) return
  try {
    const { token } = await data.get(
      `${Project.api}auth/users/me/hubspot-chat-token/`,
    )
    if (token) {
      window.hsConversationsSettings = {
        ...settings,
        identificationEmail: user.email,
        identificationToken: token,
      }
    }
  } catch (error) {
    console.error('Failed to identify the HubSpot chat user:', error)
  }
}

let isLoadingHubSpot = false
let openHubSpotOnLoad = false

// The HubSpot script is added in libs.js with loadImmediately: false, so the
// widget only appears once we call load(). Calls made while the token is being
// fetched share that fetch and a single load().
function loadHubSpotWidget(widgetOpen = false) {
  if (!canLoadHubSpot()) return
  openHubSpotOnLoad = openHubSpotOnLoad || widgetOpen
  if (isLoadingHubSpot) return
  isLoadingHubSpot = true
  identifyHubSpotVisitor()
    .then(() => {
      // Re-checked: the org may have changed while the token was fetched.
      if (canLoadHubSpot()) {
        window.HubSpotConversations?.widget.load({
          widgetOpen: openHubSpotOnLoad,
        })
      }
    })
    .finally(() => {
      isLoadingHubSpot = false
      openHubSpotOnLoad = false
    })
}

// Module-level so that repeated calls before the API is ready queue it only
// once.
const onHubSpotReady = () => {
  loadHubSpotWidget()
}

function showHubSpot() {
  if (window.HubSpotConversations) {
    loadHubSpotWidget()
  } else if (!window.hsConversationsOnReady?.includes(onHubSpotReady)) {
    window.hsConversationsOnReady = [
      ...(window.hsConversationsOnReady || []),
      onHubSpotReady,
    ]
  }
}

function removeHubSpot() {
  window.HubSpotConversations?.widget.remove()
}

export function hideChat() {
  hidePylon()
  removeHubSpot()
}

export function identifyChatUser() {
  const provider = getChatProvider()
  if (provider === 'hubspot') {
    hidePylon()
    showHubSpot()
  } else if (provider === 'pylon') {
    removeHubSpot()
    setupPylon()
    if (typeof window.Pylon !== 'undefined') {
      window.Pylon('showChatBubble')
    }
  } else {
    hideChat()
  }
}

export function openChat() {
  const provider = getChatProvider()
  if (provider === 'hubspot' && window.HubSpotConversations) {
    const { widget } = window.HubSpotConversations
    if (widget.status().loaded) {
      widget.open()
    } else {
      loadHubSpotWidget(true)
    }
    return
  }
  if (provider === 'pylon' && typeof window.Pylon !== 'undefined') {
    window.Pylon('show')
    setupPylon()
    return
  }
  // No chat for this org, or the widget was blocked: email beats a dead click.
  window.location.href = SUPPORT_EMAIL_URL
}

export default async function loadChat(forceDefaultAPIKey?: boolean) {
  try {
    const isWidget = document.location.href.includes('/widget')
    if (isWidget) return

    if (getChatProvider() === 'pylon') {
      const pylonId = forceDefaultAPIKey ? defaultPylonID : Project.pylonAppId
      if (pylonId) {
        await loadPylon(pylonId)
      }
    }
  } catch (error) {
    console.error('Failed to initialize chat widget:', error)
  }
}
