import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import DocPage from './components/DocPage'
import { radius } from 'common/theme/tokens'

const meta: Meta = {
  parameters: { chromatic: { disableSnapshot: true }, layout: 'padded' },
  title: 'Design System/Border Radius',
}
export default meta

const RADIUS_SCALE = Object.entries(radius).map(([, entry]) => ({
  description: entry.description,
  token: entry.value.match(/var\((--[^,)]+)/)?.[1] ?? '',
  value: entry.value.match(/,\s*(.+)\)$/)?.[1]?.trim() ?? '',
}))

export const Overview: StoryObj = {
  render: () => (
    <DocPage
      title='Border Radius Tokens'
      description={
        <>
          Defined in <code>_tokens.scss</code>. Use{' '}
          <code>{'border-radius: var(--radius-md)'}</code> in SCSS or{' '}
          <code>{'radius.md'}</code> from <code>common/theme/tokens</code> in
          TypeScript.
        </>
      }
    >
      <table className='docs-table'>
        <thead>
          <tr>
            <th>Preview</th>
            <th>Token</th>
            <th>Value</th>
            <th>Usage</th>
          </tr>
        </thead>
        <tbody>
          {RADIUS_SCALE.map(({ description, token, value }) => (
            <tr key={token}>
              <td>
                <div
                  style={{
                    background: 'var(--color-surface-muted, #eff1f4)',
                    border: '2px solid var(--color-surface-action, #6837fc)',
                    borderRadius: `var(${token})`,
                    height: 48,
                    width: 80,
                  }}
                />
              </td>
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
    </DocPage>
  ),
}
