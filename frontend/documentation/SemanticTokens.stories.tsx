import React, { useEffect, useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import DocPage from './components/DocPage'
import TokenGroup from './components/TokenGroup'
import type { TokenGroupData } from './components/TokenGroup'

const meta: Meta = {
  parameters: { chromatic: { disableSnapshot: true }, layout: 'padded' },
  title: 'Design System/Semantic Colour Tokens',
}
export default meta

// ---------------------------------------------------------------------------
// Helpers — read --color-* custom properties from the document
// ---------------------------------------------------------------------------

const TOKEN_PREFIX = '--color-'

/** Group labels derived from the second segment: --color-{group}-* */
const GROUP_LABELS: Record<string, string> = {
  border: 'Border',
  brand: 'Brand',
  danger: 'Danger',
  icon: 'Icon',
  info: 'Info',
  success: 'Success',
  surface: 'Surface',
  text: 'Text',
  warning: 'Warning',
}

/** Extract the group key from a CSS variable name. */
function groupKey(cssVar: string): string {
  return cssVar.replace(TOKEN_PREFIX, '').split('-')[0]
}

/**
 * Read all --color-* custom properties defined on :root.
 * We iterate the stylesheet rules rather than computed styles so we only
 * pick up tokens we explicitly defined (not inherited browser defaults).
 */
function readTokens(): TokenGroupData[] {
  const tokenVars = new Set<string>()

  for (const sheet of Array.from(document.styleSheets)) {
    try {
      for (const rule of Array.from(sheet.cssRules)) {
        if (
          rule instanceof CSSStyleRule &&
          (rule.selectorText === ':root' || rule.selectorText === '.dark')
        ) {
          for (let i = 0; i < rule.style.length; i++) {
            const prop = rule.style[i]
            if (prop.startsWith(TOKEN_PREFIX)) {
              tokenVars.add(prop)
            }
          }
        }
      }
    } catch {
      // cross-origin stylesheets throw — skip them
    }
  }

  const computed = getComputedStyle(document.documentElement)
  const grouped: Record<string, { cssVar: string; computed: string }[]> = {}

  Array.from(tokenVars)
    .sort()
    .forEach((cssVar) => {
      const key = groupKey(cssVar)
      if (!grouped[key]) grouped[key] = []
      grouped[key].push({
        computed: computed.getPropertyValue(cssVar).trim(),
        cssVar,
      })
    })

  // Order groups to match the SCSS file
  const ORDER = [
    'brand',
    'surface',
    'text',
    'border',
    'icon',
    'danger',
    'success',
    'warning',
    'info',
  ]
  return ORDER.filter((key) => grouped[key]).map((key) => ({
    title: GROUP_LABELS[key] || key,
    tokens: grouped[key],
  }))
}

// ---------------------------------------------------------------------------
// Story
// ---------------------------------------------------------------------------

const TokensPage: React.FC = () => {
  const [groups, setGroups] = useState<TokenGroupData[]>([])

  // No dependency array — re-runs on every render so computed values
  // update immediately when the theme is toggled via the toolbar.
  useEffect(() => {
    const timer = setTimeout(() => setGroups(readTokens()), 50)
    return () => clearTimeout(timer)
  })

  return (
    <DocPage
      title='Semantic Colour Tokens'
      description={
        <>
          Auto-generated from CSS custom properties. Source of truth:{' '}
          <code>common/theme/tokens.json</code>. Toggle the theme in the toolbar
          to see computed values update.
        </>
      }
    >
      {groups.map((group) => (
        <TokenGroup key={group.title} group={group} />
      ))}
    </DocPage>
  )
}

export const Overview: StoryObj = {
  render: () => <TokensPage />,
}
