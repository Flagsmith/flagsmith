import { Chat, GramElementsProvider } from '@gram-ai/elements'
import '@gram-ai/elements/elements.css'
import type { ElementsConfig } from '@gram-ai/elements'
import { useEffect, useSyncExternalStore } from 'react'
import data from 'common/data/base/_data'
import Project from 'common/project'
import { getDarkMode } from 'project/darkMode'

const GRAM_SHADOW_FIX_ID = 'flagsmith-gram-motion-fix'
const GRAM_MOTION_FIX_CSS = `
  /* Kill all motion entrance animations that get stuck at opacity: 0 */
  [style*="opacity: 0"], [style*="opacity:0"] {
    opacity: 1 !important;
  }
  [style*="translateY"], [style*="translateX"],
  [style*="scale(0"], [style*="rotate(-180deg)"] {
    transform: none !important;
  }
  [class*="aui-modal"], [class*="aui-sidecar"],
  [class*="aui-feedback"], [data-slot="tooltip-trigger"],
  [class*="aui-thread-welcome-message-motion"] {
    opacity: 1 !important;
    transform: none !important;
    transition: none !important;
    animation: none !important;
  }
`

// Flagsmith colours mapped to Gram's CSS custom properties.
// Injected into shadow DOM so must use :host and high-specificity selectors.
const GRAM_DARK_THEME_CSS = `
  :host, .gram-elements, :root {
    --background: #101628 !important;
    --foreground: #ffffff !important;
    --card: #15192b !important;
    --card-foreground: #ffffff !important;
    --popover: #15192b !important;
    --popover-foreground: #ffffff !important;
    --primary: #6837fc !important;
    --primary-foreground: #ffffff !important;
    --secondary: #202839 !important;
    --secondary-foreground: #e1e1e1 !important;
    --muted: #202839 !important;
    --muted-foreground: #9da4ae !important;
    --accent: #2d3443 !important;
    --accent-foreground: #ffffff !important;
    --destructive: #ef4d56 !important;
    --border: rgba(255, 255, 255, 0.08) !important;
    --input: rgba(255, 255, 255, 0.16) !important;
    --ring: #6837fc !important;
  }
`

const GRAM_LIGHT_THEME_CSS = `
  :host, .gram-elements, :root {
    --background: #ffffff !important;
    --foreground: #1a2634 !important;
    --card: #ffffff !important;
    --card-foreground: #1a2634 !important;
    --popover: #ffffff !important;
    --popover-foreground: #1a2634 !important;
    --primary: #6837fc !important;
    --primary-foreground: #ffffff !important;
    --secondary: #fafafb !important;
    --secondary-foreground: #1E0D26 !important;
    --muted: #eff1f4 !important;
    --muted-foreground: #656d7b !important;
    --accent: #eff1f4 !important;
    --accent-foreground: #1E0D26 !important;
    --destructive: #ef4d56 !important;
    --border: #e0e3e9 !important;
    --input: #e0e3e9 !important;
    --ring: #6837fc !important;
  }
`

function injectShadowFix(root: ParentNode) {
  const isDark = getDarkMode()
  const themeCSS = isDark ? GRAM_DARK_THEME_CSS : GRAM_LIGHT_THEME_CSS
  const fullCSS = GRAM_MOTION_FIX_CSS + themeCSS

  root.querySelectorAll('*').forEach((el) => {
    const shadow = el.shadowRoot
    if (!shadow) return
    const existing = shadow.getElementById(GRAM_SHADOW_FIX_ID)
    if (existing) {
      // Update theme if it changed
      if (existing.textContent !== fullCSS) {
        existing.textContent = fullCSS
      }
      return
    }
    const style = document.createElement('style')
    style.id = GRAM_SHADOW_FIX_ID
    style.textContent = fullCSS
    shadow.appendChild(style)
    // Also recurse into shadow root for nested shadows
    injectShadowFix(shadow)
  })
}

// Subscribe to dark mode changes on document.body
function useDarkMode(): boolean {
  return useSyncExternalStore(
    (callback) => {
      const observer = new MutationObserver(callback)
      observer.observe(document.body, {
        attributeFilter: ['class'],
        attributes: true,
      })
      return () => observer.disconnect()
    },
    () => getDarkMode(),
  )
}

const getSession = async () => {
  const headers: Record<string, string> = {
    'Gram-Project': Project.gramProjectSlug,
  }

  if (data.token && !Project.cookieAuthEnabled) {
    headers.Authorization = `Token ${data.token}`
  }
  return fetch('/api/gram/session', {
    headers,
    method: 'POST',
  })
    .then((res) => res.json())
    .then((d) => d.client_token)
}

export default function GramChat() {
  const isDark = useDarkMode()
  const config: ElementsConfig = {
    api: {
      session: getSession,
    },
    composer: {
      placeholder: 'Ask me anything...',
    },
    environment: {
      MCP_FLAGSMITH_SERVER_URL: Project.api?.replace(/\/api\/v1\/?$/, '') || '',
      MCP_FLAGSMITH_TOKEN_AUTH: data.token ? `Token ${data.token}` : '',
    },
    errorTracking: {
      enabled: false,
    },
    history: {
      enabled: true,
    },
    mcp: Project.gramMcpUrl,
    modal: {
      dimensions: {
        default: { height: 550, width: 650 },
      },
      position: 'bottom-left',
      title: 'Flagsmith MCP Assistant',
    },
    model: {
      defaultModel: 'anthropic/claude-sonnet-4.5',
      showModelPicker: false,
    },
    projectSlug: Project.gramProjectSlug,
    theme: {
      colorScheme: isDark ? 'dark' : 'light',
    },
    thread: {
      showFeedback: false,
    },
    variant: 'widget',
    welcome: {
      subtitle: 'How can I help you today?',
      title: 'Welcome',
    },
  }
  useEffect(() => {
    injectShadowFix(document)
    const observer = new MutationObserver(() => {
      injectShadowFix(document)
    })
    observer.observe(document.body, {
      attributeFilter: ['class'],
      attributes: true,
      childList: true,
      subtree: true,
    })

    return () => {
      observer.disconnect()
    }
  }, [])

  return (
    <GramElementsProvider config={config}>
      <Chat />
    </GramElementsProvider>
  )
}
