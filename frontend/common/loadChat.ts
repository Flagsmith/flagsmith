import flagsmith from 'flagsmith'
import Project from './project'

export async function loadCrisp(crispWebsiteId: string) {
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

export default async function loadChat() {
  try {
    // Wait for flagsmith to be initialized
    await new Promise<void>((resolve) => {
      if (flagsmith.getAllFlags()) {
        resolve()
      } else {
        const checkInterval = setInterval(() => {
          if (flagsmith.getAllFlags()) {
            clearInterval(checkInterval)
            resolve()
          }
        }, 100)
      }
    })

    const usePylon = flagsmith.hasFeature('pylon_chat')

    if (usePylon && Project.pylonAppId) {
      await loadPylon(Project.pylonAppId)
    } else if (Project.crispChat) {
      await loadCrisp(Project.crispChat)
    }
  } catch (error) {
    console.error('Failed to initialize chat widget:', error)
  }
}
