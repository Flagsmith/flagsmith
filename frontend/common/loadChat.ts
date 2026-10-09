declare global {
  interface Window {
    Pylon?: ((...args: unknown[]) => void) & { q?: unknown[][] }
    pylon?: { chat_settings: Record<string, string | undefined> }
    hsConversationsSettings?: { loadImmediately?: boolean }
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

// The HubSpot script is added in libs.js with loadImmediately: false, so the
// widget only appears once we call load().
function showHubSpot() {
  const load = () => {
    const widget = window.HubSpotConversations?.widget
    // Re-checked: the org may have changed before the API became ready.
    if (widget && getChatProvider() === 'hubspot' && !widget.status().loaded) {
      widget.load()
    }
  }
  if (window.HubSpotConversations) {
    load()
  } else {
    window.hsConversationsOnReady = [
      ...(window.hsConversationsOnReady || []),
      load,
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
      widget.load({ widgetOpen: true })
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
