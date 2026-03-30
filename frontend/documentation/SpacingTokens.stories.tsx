import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import DocPage from './components/DocPage'
import { space } from 'common/theme/tokens'

const meta: Meta = {
  parameters: { chromatic: { disableSnapshot: true }, layout: 'padded' },
  title: 'Design System/Spacing',
}
export default meta

const SPACING_SCALE = Object.entries(space).map(([, entry]) => ({
  description: entry.description,
  token: entry.value.match(/var\((--[^,)]+)/)?.[1] ?? '',
  value: entry.value.match(/,\s*(.+)\)$/)?.[1]?.trim() ?? '',
}))

// ---------------------------------------------------------------------------
// Stories
// ---------------------------------------------------------------------------

export const Overview: StoryObj = {
  render: () => (
    <DocPage
      title='Spacing Tokens'
      description={
        <>
          4px base grid. Defined in <code>_tokens.scss</code> as CSS custom
          properties. Use <code>var(--space-4)</code> in SCSS or{' '}
          <code>space[4]</code> from <code>common/theme/tokens</code> in
          TypeScript. Names follow the Tailwind convention.
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
          {SPACING_SCALE.map(({ description, token, value }) => (
            <tr key={token}>
              <td>
                <div
                  style={{
                    background: 'var(--color-surface-action, #6837fc)',
                    borderRadius: 2,
                    height: 16,
                    width: `var(${token})`,
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

      <h3 style={{ marginTop: 32 }}>Pairing rules</h3>
      <ul>
        <li>
          <strong>Icon-to-text gap:</strong> <code>--space-1</code> (4px) or{' '}
          <code>--space-2</code> (8px)
        </li>
        <li>
          <strong>Component inner padding:</strong> <code>--space-3</code>{' '}
          (12px) to <code>--space-4</code> (16px)
        </li>
        <li>
          <strong>Between components:</strong> <code>--space-4</code> (16px) to{' '}
          <code>--space-6</code> (24px)
        </li>
        <li>
          <strong>Page sections:</strong> <code>--space-8</code> (32px) and
          above
        </li>
      </ul>
    </DocPage>
  ),
}
