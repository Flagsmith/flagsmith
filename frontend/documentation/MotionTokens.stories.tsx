import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import DocPage from './components/DocPage'
import { duration, easing } from 'common/theme/tokens'

const meta: Meta = {
  parameters: { chromatic: { disableSnapshot: true }, layout: 'padded' },
  title: 'Design System/Motion',
}
export default meta

const DURATION_SCALE = Object.entries(duration).map(([, entry]) => ({
  description: entry.description,
  token: entry.value.match(/var\((--[^,)]+)/)?.[1] ?? '',
  value: entry.value.match(/,\s*(.+)\)$/)?.[1]?.trim() ?? '',
}))

const EASING_SCALE = Object.entries(easing).map(([, entry]) => ({
  description: entry.description,
  token: entry.value.match(/var\((--[^,)]+)/)?.[1] ?? '',
  value: entry.value.match(/var\((--[^,)]+)\)/)?.[0] ?? entry.value,
}))

const DemoBox: React.FC<{
  duration: string
  easing: string
  label: string
}> = ({ duration, easing, label }) => {
  const [active, setActive] = useState(false)

  return (
    <div
      onClick={() => setActive((v) => !v)}
      role='button'
      style={{
        background: active
          ? 'var(--color-surface-action, #6837fc)'
          : 'var(--color-surface-muted, #eff1f4)',
        borderRadius: 'var(--radius-md, 6px)',
        color: active
          ? 'var(--color-text-on-fill, #fff)'
          : 'var(--color-text-default)',
        cursor: 'pointer',
        fontSize: 13,
        fontWeight: 600,
        padding: '12px 16px',
        textAlign: 'center',
        transform: active ? 'scale(1.05)' : 'scale(1)',
        transition: `all ${duration} ${easing}`,
        userSelect: 'none',
      }}
      tabIndex={0}
    >
      {label} — click me
    </div>
  )
}

export const Overview: StoryObj = {
  render: () => (
    <DocPage
      title='Motion Tokens'
      description={
        <>
          Duration and easing tokens for consistent animation. Defined in{' '}
          <code>_tokens.scss</code>. Pair a duration with an easing:{' '}
          <code>
            {'transition: all var(--duration-normal) var(--easing-standard)'}
          </code>
        </>
      }
    >
      <h3>Duration</h3>
      <table className='docs-table'>
        <thead>
          <tr>
            <th>Token</th>
            <th>Value</th>
            <th>Usage</th>
          </tr>
        </thead>
        <tbody>
          {DURATION_SCALE.map(({ description, token, value }) => (
            <tr key={token}>
              <td>
                <code>{token}</code>
              </td>
              <td>
                <code>{value}</code>
              </td>
              <td
                style={{
                  color: 'var(--color-text-secondary)',
                  fontSize: 13,
                }}
              >
                {description}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3 style={{ marginTop: 32 }}>Easing</h3>
      <table className='docs-table'>
        <thead>
          <tr>
            <th>Token</th>
            <th>Value</th>
            <th>Usage</th>
          </tr>
        </thead>
        <tbody>
          {EASING_SCALE.map(({ description, token, value }) => (
            <tr key={token}>
              <td>
                <code>{token}</code>
              </td>
              <td>
                <code style={{ fontSize: 11 }}>{value}</code>
              </td>
              <td
                style={{
                  color: 'var(--color-text-secondary)',
                  fontSize: 13,
                }}
              >
                {description}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3 style={{ marginTop: 32 }}>Interactive demo</h3>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
        Click each box to see the duration + easing combination in action.
      </p>
      <div
        style={{
          display: 'grid',
          gap: 12,
          gridTemplateColumns: 'repeat(3, 1fr)',
          marginTop: 12,
        }}
      >
        <DemoBox
          duration='100ms'
          easing='cubic-bezier(0.2, 0, 0.38, 0.9)'
          label='Fast + Standard'
        />
        <DemoBox
          duration='200ms'
          easing='cubic-bezier(0.0, 0, 0.38, 0.9)'
          label='Normal + Entrance'
        />
        <DemoBox
          duration='300ms'
          easing='cubic-bezier(0.2, 0, 1, 0.9)'
          label='Slow + Exit'
        />
      </div>
    </DocPage>
  ),
}
