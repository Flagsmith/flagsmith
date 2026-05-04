declare global {
  interface Window {
    Pylon?: ((...args: unknown[]) => void) & { q?: unknown[][] }
    pylon?: { chat_settings: Record<string, string | undefined> }
  }
}

import flagsmith from '@flagsmith/flagsmith'
import AccountStore from './stores/account-store'
import getUserDisplayName from './utils/getUserDisplayName'
import Utils, { planNames } from './utils/utils'
import { AccountModel } from './types/responses'
import Project from './project'

const defaultPylonID = '028babb7-d93f-4e32-be6a-59db190a084f'

function isFreePlan(): boolean {
  const plan = AccountStore.getActiveOrgPlan()
  return Utils.getPlanName(plan) === planNames.free
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

export function hidePylon() {
  if (typeof window.Pylon !== 'undefined') {
    window.Pylon('hideChatBubble')
  }
}

export function identifyChatUser() {
  if (flagsmith.hasFeature('pylon_chat') && !isFreePlan()) {
    setupPylon()
    if (typeof window.Pylon !== 'undefined') {
      window.Pylon('showChatBubble')
    }
  } else {
    hidePylon()
  }
}

export function openChat() {
  if (
    flagsmith.hasFeature('pylon_chat') &&
    !isFreePlan() &&
    typeof window.Pylon !== 'undefined'
  ) {
    window.Pylon('show')
    setupPylon()
  }
}

export default async function loadChat(forceDefaultAPIKey?: boolean) {
  try {
    const isWidget = document.location.href.includes('/widget')
    if (isWidget) return

    if (flagsmith.hasFeature('pylon_chat') && !isFreePlan()) {
      const pylonId = forceDefaultAPIKey ? defaultPylonID : Project.pylonAppId
      if (pylonId) {
        await loadPylon(pylonId)
      }
    }
  } catch (error) {
    console.error('Failed to initialize chat widget:', error)
  }
}
