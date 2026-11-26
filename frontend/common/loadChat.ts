declare global {
  interface Window {
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
import { getStore } from './store'
import { getHubspotChatToken } from './services/useHubspotChatToken'
import Utils from './utils/utils'
import { AccountModel, HubspotChatToken } from './types/responses'

const SUPPORT_EMAIL_URL = 'mailto:support@flagsmith.com'

export type ChatProvider = 'hubspot'

// hubspot_chat's value sets who gets HubSpot chat: "all" opens it to every
// plan, anything else (including no value) keeps it to paid plans.
const HUBSPOT_CHAT_ALL_PLANS = 'all'

export function getChatProvider(): ChatProvider | null {
  const isFreePlan = Utils.isOrgOnFreePlan()
  if (Utils.getFlagsmithHasFeature('hubspot_chat')) {
    const audience = `${Utils.getFlagsmithValue('hubspot_chat') ?? ''}`
      .trim()
      .toLowerCase()
    return audience === HUBSPOT_CHAT_ALL_PLANS || !isFreePlan ? 'hubspot' : null
  }
  return null
}

let isLoadingHubSpot = false
let openHubSpotOnLoad = false
// load() was called. status().loaded stays false until HubSpot's iframe is
// ready, so it can't tell us on its own.
let hasRequestedHubSpotLoad = false
// Bumped when the widget is removed (e.g. logout), so a token fetched for
// the previous user is never used.
let hubSpotGeneration = 0

function canLoadHubSpot() {
  const widget = window.HubSpotConversations?.widget
  return (
    !!widget &&
    getChatProvider() === 'hubspot' &&
    !hasRequestedHubSpotLoad &&
    !widget.status().loaded
  )
}

// HubSpot reads the identity when load() is called, so tickets get a contact
// instead of "Unknown Visitor".
function setHubSpotIdentity(identity?: HubspotChatToken) {
  const settings = { ...window.hsConversationsSettings }
  delete settings.identificationEmail
  delete settings.identificationToken
  window.hsConversationsSettings = identity
    ? {
        ...settings,
        identificationEmail: identity.email,
        identificationToken: identity.token,
      }
    : settings
}

// Without a token the widget still loads, just anonymously. A 404 means the
// API has no HubSpot token configured (e.g. self-hosted), so it isn't logged.
async function fetchHubSpotIdentity(): Promise<HubspotChatToken | undefined> {
  const user = AccountStore.getUser() as AccountModel | undefined
  if (!user?.id) return
  try {
    const { data, error } = await getHubspotChatToken(
      getStore(),
      { userId: user.id },
      { subscribe: false },
    )
    if (error && error.status !== 404) {
      console.error('Failed to identify the HubSpot chat user:', error)
    }
    return data
  } catch (error) {
    console.error('Failed to identify the HubSpot chat user:', error)
  }
}

// The HubSpot script is added in libs.js with loadImmediately: false, so the
// widget only appears once we call load(). Calls made while the token is being
// fetched share that fetch and a single load().
function loadHubSpotWidget(widgetOpen = false) {
  if (!canLoadHubSpot()) return
  openHubSpotOnLoad = openHubSpotOnLoad || widgetOpen
  if (isLoadingHubSpot) return
  isLoadingHubSpot = true
  const generation = hubSpotGeneration
  fetchHubSpotIdentity().then((identity) => {
    // Removed during the fetch: any newer call has started its own.
    if (generation !== hubSpotGeneration) return
    isLoadingHubSpot = false
    const widgetOpenOnLoad = openHubSpotOnLoad
    openHubSpotOnLoad = false
    // Re-checked: the org may have changed while the token was fetched.
    if (!canLoadHubSpot()) return
    setHubSpotIdentity(identity)
    hasRequestedHubSpotLoad = true
    window.HubSpotConversations?.widget.load({ widgetOpen: widgetOpenOnLoad })
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
  hubSpotGeneration += 1
  isLoadingHubSpot = false
  openHubSpotOnLoad = false
  hasRequestedHubSpotLoad = false
  setHubSpotIdentity()
  window.HubSpotConversations?.widget.remove()
}

export function hideChat() {
  removeHubSpot()
}

export function identifyChatUser() {
  if (getChatProvider() === 'hubspot') {
    showHubSpot()
  } else {
    hideChat()
  }
}

export function openChat() {
  const provider = getChatProvider()
  if (provider === 'hubspot' && window.HubSpotConversations) {
    const { widget } = window.HubSpotConversations
    // Once load() was called, open() is all that's left to do.
    if (widget.status().loaded || hasRequestedHubSpotLoad) {
      widget.open()
    } else {
      loadHubSpotWidget(true)
    }
    return
  }
  // No chat for this org, or the widget was blocked: email beats a dead click.
  window.location.href = SUPPORT_EMAIL_URL
}
