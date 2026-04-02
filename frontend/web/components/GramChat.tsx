import { Chat, GramElementsProvider } from '@gram-ai/elements'
import '@gram-ai/elements/elements.css'
import type { ElementsConfig } from '@gram-ai/elements'
import { useEffect, useMemo, useRef, useSyncExternalStore } from 'react'
import data from 'common/data/base/_data'
import Project from 'common/project'
import { getDarkMode } from 'project/darkMode'
import { GRAM_DARK_THEME_CSS, GRAM_LIGHT_THEME_CSS } from './gram-theme'

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
  /* Nudge the bubble up to avoid overlap with bottom bar */
  .aui-modal-anchor {
    bottom: 26px !important;
  }
  [class*="aui-modal-anchor"],
  [class*="fixed"][class*="bottom"] {
    bottom: 26px !important;
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

const getSession = async ({ projectSlug }: { projectSlug: string }) => {
  const headers: Record<string, string> = {
    'Gram-Project': projectSlug,
  }
  if (data.token && !Project.cookieAuthEnabled) {
    headers.Authorization = `Token ${data.token}`
  }
  const res = await fetch('/api/gram/session', {
    headers,
    method: 'POST',
  })
  const json = await res.json()
  return json.client_token
}

export default function GramChat() {
  const isDark = useDarkMode()
  const containerRef = useRef<HTMLDivElement>(null)

  const config: ElementsConfig = useMemo(
    () => ({
      api: {
        session: getSession,
      },
      composer: {
        placeholder: 'Ask me anything...',
      },
      environment: {
        MCP_FLAGSMITH_SERVER_URL:
          Project.api?.replace(/\/api\/v1\/?$/, '') || '',
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
        position: 'bottom-left' as const,
        title: 'Flagsmith MCP Assistant',
      },
      model: {
        defaultModel: 'anthropic/claude-sonnet-4.5' as const,
        showModelPicker: false,
      },
      projectSlug: Project.gramProjectSlug,
      theme: {
        colorScheme: isDark ? ('dark' as const) : ('light' as const),
      },
      thread: {
        showFeedback: false,
      },
      variant: 'widget' as const,
      welcome: {
        subtitle: 'How can I help you today?',
        title: 'Welcome',
      },
    }),
    [isDark],
  )

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    injectShadowFix(container)
    const observer = new MutationObserver(() => {
      injectShadowFix(container)
    })
    observer.observe(container, {
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
    <div ref={containerRef}>
      <GramElementsProvider config={config}>
        <Chat />
      </GramElementsProvider>
    </div>
  )
}
