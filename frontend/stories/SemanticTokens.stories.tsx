import React, { useEffect, useState } from 'react'
import type { Meta, StoryObj } from '@storybook/react-webpack5'

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Design System/Semantic Tokens',
}
export default meta

// ---------------------------------------------------------------------------
// Helpers — read --color-* custom properties from the document
// ---------------------------------------------------------------------------

const TOKEN_PREFIX = '--color-'

type TokenEntry = { cssVar: string; computed: string }
type TokenGroup = { title: string; tokens: TokenEntry[] }

/** Group labels derived from the second segment: --color-{group}-* */
const GROUP_LABELS: Record<string, string> = {
  border: 'Border',
  brand: 'Brand',
  danger: 'Danger',
  info: 'Info',
  success: 'Success',
  surface: 'Surface',
  text: 'Text',
  warning: 'Warning',
}

/** Extract the group key from a CSS variable name. */
function groupKey(cssVar: string): string {
  // --color-brand-default → brand
  return cssVar.replace(TOKEN_PREFIX, '').split('-')[0]
}

/**
 * Read all --color-* custom properties defined on :root.
 * We iterate the stylesheet rules rather than computed styles so we only
 * pick up tokens we explicitly defined (not inherited browser defaults).
 */
function readTokens(): TokenGroup[] {
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
  const grouped: Record<string, TokenEntry[]> = {}

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

  // Order groups to match the SCSS file: brand, surface, text, border, then feedback
  const ORDER = [
    'brand',
    'surface',
    'text',
    'border',
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
// Components
// ---------------------------------------------------------------------------

const TokenSwatch: React.FC<{ token: TokenEntry }> = ({ token }) => (
  <div
    style={{
      alignItems: 'center',
      borderBottom:
        '1px solid var(--color-border-default, rgba(101,109,123,0.16))',
      display: 'grid',
      gap: 12,
      gridTemplateColumns: '48px 1fr 1fr',
      padding: '8px 0',
    }}
  >
    <div
      style={{
        background: `var(${token.cssVar})`,
        border: '1px solid rgba(128,128,128,0.2)',
        borderRadius: 8,
        height: 40,
        width: 40,
      }}
    />
    <code
      style={{
        color: 'var(--color-text-default, #1a2634)',
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      {token.cssVar}
    </code>
    <code
      style={{
        color: 'var(--color-text-secondary, #656d7b)',
        fontSize: 11,
      }}
    >
      {token.computed}
    </code>
  </div>
)

const TokenGroupSection: React.FC<{ group: TokenGroup }> = ({ group }) => (
  <div style={{ marginBottom: 32 }}>
    <h3
      style={{
        color: 'var(--color-text-default, #1a2634)',
        fontSize: 16,
        fontWeight: 700,
        marginBottom: 12,
      }}
    >
      {group.title}
    </h3>
    <div
      style={{
        borderBottom:
          '2px solid var(--color-border-strong, rgba(101,109,123,0.24))',
        display: 'grid',
        gap: 12,
        gridTemplateColumns: '48px 1fr 1fr',
        paddingBottom: 6,
      }}
    >
      <span />
      {['Token', 'Computed value'].map((h) => (
        <span
          key={h}
          style={{
            color: 'var(--color-text-secondary, #656d7b)',
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
          }}
        >
          {h}
        </span>
      ))}
    </div>
    {group.tokens.map((token) => (
      <TokenSwatch key={token.cssVar} token={token} />
    ))}
  </div>
)

// ---------------------------------------------------------------------------
// Story
// ---------------------------------------------------------------------------

const TokensPage: React.FC = () => {
  const [groups, setGroups] = useState<TokenGroup[]>([])

  useEffect(() => {
    // Small delay to ensure styles are loaded after theme toggle
    const timer = setTimeout(() => setGroups(readTokens()), 50)
    return () => clearTimeout(timer)
  })

  return (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 800 }}>
      <h2
        style={{ color: 'var(--color-text-default, #1a2634)', marginBottom: 4 }}
      >
        Semantic Colour Tokens
      </h2>
      <p
        style={{
          color: 'var(--color-text-secondary, #656d7b)',
          fontSize: 14,
          marginBottom: 24,
        }}
      >
        Auto-generated from CSS custom properties defined in{' '}
        <code style={{ color: 'inherit' }}>web/styles/_tokens.scss</code>.
        Toggle the theme in the toolbar to see computed values update.
      </p>
      {groups.map((group) => (
        <TokenGroupSection key={group.title} group={group} />
      ))}
    </div>
  )
}

export const Overview: StoryObj = {
  render: () => <TokensPage />,
}
