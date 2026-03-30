import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import DocPage from './components/DocPage'
import { shadow } from 'common/theme/tokens'

const meta: Meta = {
  parameters: { chromatic: { disableSnapshot: true }, layout: 'padded' },
  title: 'Design System/Elevation',
}
export default meta

const SHADOW_SCALE = Object.entries(shadow).map(([, entry]) => ({
  description: entry.description,
  token: entry.value.match(/var\((--[^,)]+)/)?.[1] ?? '',
  value: entry.value.match(/,\s*(.+)\)$/)?.[1]?.trim() ?? entry.value,
}))

export const Overview: StoryObj = {
  render: () => (
    <DocPage
      title='Elevation / Shadow Tokens'
      description={
        <>
          Four elevation levels. Dark mode uses stronger shadows since surface
          colour differentiation replaces visual lift. Defined in{' '}
          <code>_tokens.scss</code> with <code>.dark</code> overrides.
        </>
      }
    >
      <div
        style={{
          display: 'grid',
          gap: 24,
          gridTemplateColumns: 'repeat(auto-fit, minmax(260, 1fr))',
        }}
      >
        {SHADOW_SCALE.map(({ description, token, value }) => (
          <div
            key={token}
            style={{
              background: 'var(--color-surface-default, #fff)',
              borderRadius: 'var(--radius-lg, 8px)',
              boxShadow: `var(${token})`,
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              padding: 24,
            }}
          >
            <code style={{ fontSize: 13, fontWeight: 600 }}>{token}</code>
            <code
              style={{
                color: 'var(--color-text-tertiary)',
                fontSize: 11,
              }}
            >
              {value}
            </code>
            <span
              style={{
                color: 'var(--color-text-secondary)',
                fontSize: 13,
                marginTop: 4,
              }}
            >
              {description}
            </span>
          </div>
        ))}
      </div>

      <h3 style={{ marginTop: 32 }}>Dark mode strategy</h3>
      <p>
        In dark mode, shadows are harder to perceive. The dark overrides use
        stronger opacity values (0.20–0.40 vs 0.05–0.20). Additionally, higher
        elevation surfaces should use progressively lighter background colours
        (e.g. <code>--color-surface-emphasis</code> for modals) to maintain
        visual hierarchy without relying solely on shadows.
      </p>
    </DocPage>
  ),
}
