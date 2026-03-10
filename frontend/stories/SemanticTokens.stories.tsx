import React from 'react'
import type { Meta, StoryObj } from '@storybook/react-webpack5'

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Design System/Semantic Tokens',
}
export default meta

// ---------------------------------------------------------------------------
// Token definitions — mirrors web/styles/_tokens.scss
// ---------------------------------------------------------------------------

type Token = {
  name: string
  cssVar: string
  light: string
  dark: string
}

type TokenGroup = {
  title: string
  description: string
  tokens: Token[]
}

const tokenGroups: TokenGroup[] = [
  {
    description: 'Primary brand colour for actions, links, and focus states.',
    title: 'Brand',
    tokens: [
      {
        cssVar: '--color-brand-default',
        dark: '#906af6',
        light: '#6837fc',
        name: 'brand-default',
      },
      {
        cssVar: '--color-brand-hover',
        dark: '#6837fc',
        light: '#4e25db',
        name: 'brand-hover',
      },
      {
        cssVar: '--color-brand-active',
        dark: '#4e25db',
        light: '#3919b7',
        name: 'brand-active',
      },
      {
        cssVar: '--color-brand-subtle',
        dark: 'rgba(255,255,255,0.08)',
        light: 'rgba(104,55,252,0.08)',
        name: 'brand-subtle',
      },
      {
        cssVar: '--color-brand-muted',
        dark: 'rgba(255,255,255,0.16)',
        light: 'rgba(104,55,252,0.16)',
        name: 'brand-muted',
      },
    ],
  },
  {
    description: 'Backgrounds for pages, panels, cards, and inputs.',
    title: 'Surface',
    tokens: [
      {
        cssVar: '--color-surface-default',
        dark: '#101628',
        light: '#ffffff',
        name: 'surface-default',
      },
      {
        cssVar: '--color-surface-subtle',
        dark: '#15192b',
        light: '#fafafb',
        name: 'surface-subtle',
      },
      {
        cssVar: '--color-surface-muted',
        dark: '#161d30',
        light: '#eff1f4',
        name: 'surface-muted',
      },
      {
        cssVar: '--color-surface-emphasis',
        dark: '#202839',
        light: '#e0e3e9',
        name: 'surface-emphasis',
      },
    ],
  },
  {
    description:
      'Foreground colours for headings, body, captions, and inverted text.',
    title: 'Text',
    tokens: [
      {
        cssVar: '--color-text-default',
        dark: '#ffffff',
        light: '#1a2634',
        name: 'text-default',
      },
      {
        cssVar: '--color-text-secondary',
        dark: '#9da4ae',
        light: '#656d7b',
        name: 'text-secondary',
      },
      {
        cssVar: '--color-text-tertiary',
        dark: 'rgba(255,255,255,0.48)',
        light: '#9da4ae',
        name: 'text-tertiary',
      },
      {
        cssVar: '--color-text-on-fill',
        dark: '#ffffff',
        light: '#ffffff',
        name: 'text-on-fill',
      },
    ],
  },
  {
    description: 'Strokes for inputs, panels, dividers.',
    title: 'Border',
    tokens: [
      {
        cssVar: '--color-border-default',
        dark: 'rgba(255,255,255,0.16)',
        light: 'rgba(101,109,123,0.16)',
        name: 'border-default',
      },
      {
        cssVar: '--color-border-strong',
        dark: 'rgba(255,255,255,0.24)',
        light: 'rgba(101,109,123,0.24)',
        name: 'border-strong',
      },
    ],
  },
  {
    description: 'Status colours for alerts, badges, and validation.',
    title: 'Feedback',
    tokens: [
      {
        cssVar: '--color-danger-default',
        dark: '#ef4d56',
        light: '#ef4d56',
        name: 'danger-default',
      },
      {
        cssVar: '--color-danger-subtle',
        dark: 'rgba(34,23,40,1)',
        light: 'rgba(239,77,86,0.08)',
        name: 'danger-subtle',
      },
      {
        cssVar: '--color-success-default',
        dark: '#27ab95',
        light: '#27ab95',
        name: 'success-default',
      },
      {
        cssVar: '--color-success-subtle',
        dark: 'rgba(17,32,46,1)',
        light: 'rgba(39,171,149,0.08)',
        name: 'success-subtle',
      },
      {
        cssVar: '--color-warning-default',
        dark: '#ff9f43',
        light: '#ff9f43',
        name: 'warning-default',
      },
      {
        cssVar: '--color-warning-subtle',
        dark: 'rgba(34,31,39,1)',
        light: 'rgba(255,159,67,0.08)',
        name: 'warning-subtle',
      },
      {
        cssVar: '--color-info-default',
        dark: '#0aaddf',
        light: '#0aaddf',
        name: 'info-default',
      },
      {
        cssVar: '--color-info-subtle',
        dark: 'rgba(15,32,52,1)',
        light: 'rgba(10,173,223,0.08)',
        name: 'info-subtle',
      },
    ],
  },
]

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

const TokenSwatch: React.FC<{ token: Token }> = ({ token }) => (
  <div
    style={{
      alignItems: 'center',
      borderBottom:
        '1px solid var(--color-border-default, rgba(101,109,123,0.16))',
      display: 'grid',
      gap: 12,
      gridTemplateColumns: '48px 1fr 1fr 1fr',
      padding: '8px 0',
    }}
  >
    <div
      style={{
        background: `var(${token.cssVar})`,
        border: '1px solid rgba(128,128,128,0.2)',
        borderRadius: 8,
        flexShrink: 0,
        height: 40,
        width: 40,
      }}
    />
    <div>
      <code
        style={{
          color: 'var(--color-text-default, #1a2634)',
          fontSize: 12,
          fontWeight: 600,
        }}
      >
        {token.cssVar}
      </code>
    </div>
    <div>
      <div style={{ alignItems: 'center', display: 'flex', gap: 6 }}>
        <div
          style={{
            background: token.light,
            border: '1px solid rgba(128,128,128,0.2)',
            borderRadius: 3,
            height: 16,
            width: 16,
          }}
        />
        <code
          style={{
            color: 'var(--color-text-secondary, #656d7b)',
            fontSize: 11,
          }}
        >
          {token.light}
        </code>
      </div>
    </div>
    <div>
      <div style={{ alignItems: 'center', display: 'flex', gap: 6 }}>
        <div
          style={{
            background: token.dark,
            border: '1px solid rgba(128,128,128,0.2)',
            borderRadius: 3,
            height: 16,
            width: 16,
          }}
        />
        <code
          style={{
            color: 'var(--color-text-secondary, #656d7b)',
            fontSize: 11,
          }}
        >
          {token.dark}
        </code>
      </div>
    </div>
  </div>
)

const TokenGroupSection: React.FC<{ group: TokenGroup }> = ({ group }) => (
  <div style={{ marginBottom: 32 }}>
    <h3
      style={{
        color: 'var(--color-text-default, #1a2634)',
        fontSize: 16,
        fontWeight: 700,
        marginBottom: 4,
      }}
    >
      {group.title}
    </h3>
    <p
      style={{
        color: 'var(--color-text-secondary, #656d7b)',
        fontSize: 13,
        marginBottom: 12,
        marginTop: 0,
      }}
    >
      {group.description}
    </p>

    {/* Column headers */}
    <div
      style={{
        borderBottom:
          '2px solid var(--color-border-strong, rgba(101,109,123,0.24))',
        display: 'grid',
        gap: 12,
        gridTemplateColumns: '48px 1fr 1fr 1fr',
        paddingBottom: 6,
      }}
    >
      <span />
      {['Token', 'Light', 'Dark'].map((h) => (
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
      <TokenSwatch key={token.name} token={token} />
    ))}
  </div>
)

// ---------------------------------------------------------------------------
// Live preview — shows tokens responding to the active theme
// ---------------------------------------------------------------------------

const LivePreview: React.FC = () => (
  <div
    style={{
      background: 'var(--color-surface-default)',
      border: '1px solid var(--color-border-default)',
      borderRadius: 8,
      marginBottom: 32,
      padding: 24,
    }}
  >
    <h4
      style={{
        color: 'var(--color-text-default)',
        fontSize: 14,
        fontWeight: 700,
        marginBottom: 16,
      }}
    >
      Live preview — toggle theme to see tokens adapt
    </h4>
    <div
      style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}
    >
      <div
        style={{
          background: 'var(--color-brand-default)',
          borderRadius: 6,
          color: 'var(--color-text-on-fill)',
          fontSize: 14,
          fontWeight: 700,
          padding: '8px 20px',
        }}
      >
        Brand button
      </div>
      <div
        style={{
          background: 'var(--color-surface-subtle)',
          border: '1px solid var(--color-border-default)',
          borderRadius: 6,
          color: 'var(--color-text-default)',
          fontSize: 14,
          padding: '8px 20px',
        }}
      >
        Surface card
      </div>
      <div
        style={{
          background: 'var(--color-danger-subtle)',
          borderRadius: 6,
          color: 'var(--color-danger-default)',
          fontSize: 14,
          fontWeight: 600,
          padding: '8px 20px',
        }}
      >
        Danger badge
      </div>
      <div
        style={{
          background: 'var(--color-success-subtle)',
          borderRadius: 6,
          color: 'var(--color-success-default)',
          fontSize: 14,
          fontWeight: 600,
          padding: '8px 20px',
        }}
      >
        Success badge
      </div>
    </div>
    <p
      style={{
        color: 'var(--color-text-secondary)',
        fontSize: 13,
        margin: 0,
      }}
    >
      Secondary text on{' '}
      <span
        style={{
          background: 'var(--color-surface-emphasis)',
          borderRadius: 4,
          padding: '2px 8px',
        }}
      >
        emphasis surface
      </span>
    </p>
  </div>
)

// ---------------------------------------------------------------------------
// Stories
// ---------------------------------------------------------------------------

export const Overview: StoryObj = {
  render: () => (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 960 }}>
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
        CSS custom properties that automatically adapt to light/dark mode.
        Toggle the theme in the toolbar above to preview both modes.
        <br />
        Source: <code>web/styles/_tokens.scss</code>
      </p>

      <LivePreview />

      {tokenGroups.map((group) => (
        <TokenGroupSection key={group.title} group={group} />
      ))}
    </div>
  ),
}
