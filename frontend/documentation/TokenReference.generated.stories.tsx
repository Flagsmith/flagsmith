// AUTO-GENERATED from common/theme/tokens.json — do not edit manually
// Run: npm run generate:tokens

import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import DocPage from './components/DocPage'

const meta: Meta = {
  parameters: { chromatic: { disableSnapshot: true }, layout: 'padded' },
  title: 'Design System/Token Reference (MCP)',
}
export default meta

export const AllTokens: StoryObj = {
  name: 'All tokens (MCP reference)',
  render: () => (
    <DocPage
      title='Token Reference'
      description='Complete token catalogue generated from common/theme/tokens.json. All data is inlined for Storybook MCP.'
    >
      <h3>Colour: surface</h3>
      <table className='docs-table'>
        <thead>
          <tr>
            <th>Token</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>--color-surface-default</code>
            </td>
            <td>
              <code>var(--slate-0)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-subtle</code>
            </td>
            <td>
              <code>var(--slate-50)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-muted</code>
            </td>
            <td>
              <code>var(--slate-100)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-emphasis</code>
            </td>
            <td>
              <code>var(--slate-200)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-hover</code>
            </td>
            <td>
              <code>oklch(from var(--slate-1000) l c h / 0.08)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-active</code>
            </td>
            <td>
              <code>oklch(from var(--slate-1000) l c h / 0.16)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-action</code>
            </td>
            <td>
              <code>var(--purple-600)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-action-hover</code>
            </td>
            <td>
              <code>var(--purple-700)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-action-active</code>
            </td>
            <td>
              <code>var(--purple-800)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-action-subtle</code>
            </td>
            <td>
              <code>oklch(from var(--purple-600) l c h / 0.08)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-action-muted</code>
            </td>
            <td>
              <code>oklch(from var(--purple-600) l c h / 0.16)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-danger</code>
            </td>
            <td>
              <code>oklch(from var(--red-500) l c h / 0.08)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-success</code>
            </td>
            <td>
              <code>oklch(from var(--green-500) l c h / 0.08)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-warning</code>
            </td>
            <td>
              <code>oklch(from var(--orange-500) l c h / 0.08)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-surface-info</code>
            </td>
            <td>
              <code>oklch(from var(--blue-500) l c h / 0.08)</code>
            </td>
          </tr>
        </tbody>
      </table>
      <h3>Colour: text</h3>
      <table className='docs-table'>
        <thead>
          <tr>
            <th>Token</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>--color-text-default</code>
            </td>
            <td>
              <code>var(--slate-600)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-text-secondary</code>
            </td>
            <td>
              <code>var(--slate-500)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-text-tertiary</code>
            </td>
            <td>
              <code>var(--slate-300)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-text-disabled</code>
            </td>
            <td>
              <code>var(--slate-300)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-text-action</code>
            </td>
            <td>
              <code>var(--purple-600)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-text-danger</code>
            </td>
            <td>
              <code>var(--red-500)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-text-success</code>
            </td>
            <td>
              <code>var(--green-500)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-text-warning</code>
            </td>
            <td>
              <code>var(--orange-500)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-text-info</code>
            </td>
            <td>
              <code>var(--blue-500)</code>
            </td>
          </tr>
        </tbody>
      </table>
      <h3>Colour: border</h3>
      <table className='docs-table'>
        <thead>
          <tr>
            <th>Token</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>--color-border-default</code>
            </td>
            <td>
              <code>oklch(from var(--slate-500) l c h / 0.16)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-border-strong</code>
            </td>
            <td>
              <code>oklch(from var(--slate-500) l c h / 0.24)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-border-disabled</code>
            </td>
            <td>
              <code>oklch(from var(--slate-500) l c h / 0.08)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-border-action</code>
            </td>
            <td>
              <code>var(--purple-600)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-border-danger</code>
            </td>
            <td>
              <code>var(--red-500)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-border-success</code>
            </td>
            <td>
              <code>var(--green-500)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-border-warning</code>
            </td>
            <td>
              <code>var(--orange-500)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-border-info</code>
            </td>
            <td>
              <code>var(--blue-500)</code>
            </td>
          </tr>
        </tbody>
      </table>
      <h3>Colour: icon</h3>
      <table className='docs-table'>
        <thead>
          <tr>
            <th>Token</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>--color-icon-default</code>
            </td>
            <td>
              <code>var(--slate-600)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-icon-secondary</code>
            </td>
            <td>
              <code>var(--slate-500)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-icon-disabled</code>
            </td>
            <td>
              <code>var(--slate-300)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-icon-action</code>
            </td>
            <td>
              <code>var(--purple-600)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-icon-danger</code>
            </td>
            <td>
              <code>var(--red-500)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-icon-success</code>
            </td>
            <td>
              <code>var(--green-500)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-icon-warning</code>
            </td>
            <td>
              <code>var(--orange-500)</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>--color-icon-info</code>
            </td>
            <td>
              <code>var(--blue-500)</code>
            </td>
          </tr>
        </tbody>
      </table>
      <h3>Chart colours</h3>
      <table className='docs-table'>
        <thead>
          <tr>
            <th>Token</th>
            <th>Value</th>
            <th>Usage</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>--color-chart-1</code>
            </td>
            <td>
              <code>#0aaddf</code>
            </td>
            <td>First series in charts. Blue.</td>
          </tr>
          <tr>
            <td>
              <code>--color-chart-2</code>
            </td>
            <td>
              <code>#ef4d56</code>
            </td>
            <td>Second series. Red.</td>
          </tr>
          <tr>
            <td>
              <code>--color-chart-3</code>
            </td>
            <td>
              <code>#27ab95</code>
            </td>
            <td>Third series. Green.</td>
          </tr>
          <tr>
            <td>
              <code>--color-chart-4</code>
            </td>
            <td>
              <code>#ff9f43</code>
            </td>
            <td>Fourth series. Orange.</td>
          </tr>
          <tr>
            <td>
              <code>--color-chart-5</code>
            </td>
            <td>
              <code>#7a4dfc</code>
            </td>
            <td>Fifth series. Purple.</td>
          </tr>
          <tr>
            <td>
              <code>--color-chart-6</code>
            </td>
            <td>
              <code>#0b8bb2</code>
            </td>
            <td>Sixth series. Blue dark.</td>
          </tr>
          <tr>
            <td>
              <code>--color-chart-7</code>
            </td>
            <td>
              <code>#e61b26</code>
            </td>
            <td>Seventh series. Red dark.</td>
          </tr>
          <tr>
            <td>
              <code>--color-chart-8</code>
            </td>
            <td>
              <code>#13787b</code>
            </td>
            <td>Eighth series. Green dark.</td>
          </tr>
          <tr>
            <td>
              <code>--color-chart-9</code>
            </td>
            <td>
              <code>#fa810c</code>
            </td>
            <td>Ninth series. Orange dark.</td>
          </tr>
          <tr>
            <td>
              <code>--color-chart-10</code>
            </td>
            <td>
              <code>#6837fc</code>
            </td>
            <td>Tenth series. Purple dark.</td>
          </tr>
        </tbody>
      </table>
      <h3>Radius</h3>
      <table className='docs-table'>
        <thead>
          <tr>
            <th>Token</th>
            <th>Value</th>
            <th>Usage</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>--radius-none</code>
            </td>
            <td>
              <code>0px</code>
            </td>
            <td>Sharp corners. Tables, dividers.</td>
          </tr>
          <tr>
            <td>
              <code>--radius-xs</code>
            </td>
            <td>
              <code>2px</code>
            </td>
            <td>Barely rounded. Badges, tags.</td>
          </tr>
          <tr>
            <td>
              <code>--radius-sm</code>
            </td>
            <td>
              <code>4px</code>
            </td>
            <td>Buttons, inputs, small interactive elements.</td>
          </tr>
          <tr>
            <td>
              <code>--radius-md</code>
            </td>
            <td>
              <code>6px</code>
            </td>
            <td>Default component radius. Cards, dropdowns, tooltips.</td>
          </tr>
          <tr>
            <td>
              <code>--radius-lg</code>
            </td>
            <td>
              <code>8px</code>
            </td>
            <td>Large cards, panels.</td>
          </tr>
          <tr>
            <td>
              <code>--radius-xl</code>
            </td>
            <td>
              <code>10px</code>
            </td>
            <td>Extra-large containers.</td>
          </tr>
          <tr>
            <td>
              <code>--radius-2xl</code>
            </td>
            <td>
              <code>18px</code>
            </td>
            <td>Modals.</td>
          </tr>
          <tr>
            <td>
              <code>--radius-full</code>
            </td>
            <td>
              <code>9999px</code>
            </td>
            <td>Pill shapes, avatars, circular elements.</td>
          </tr>
        </tbody>
      </table>
      <h3>Shadow</h3>
      <table className='docs-table'>
        <thead>
          <tr>
            <th>Token</th>
            <th>Value</th>
            <th>Usage</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>--shadow-sm</code>
            </td>
            <td>
              <code>
                0px 1px 2px oklch(from var(--slate-1000) l c h / 0.05)
              </code>
            </td>
            <td>Subtle lift. Buttons on hover, input focus ring companion.</td>
          </tr>
          <tr>
            <td>
              <code>--shadow-md</code>
            </td>
            <td>
              <code>
                0px 4px 8px oklch(from var(--slate-1000) l c h / 0.12)
              </code>
            </td>
            <td>
              Cards, dropdowns, popovers. Default elevation for floating
              elements.
            </td>
          </tr>
          <tr>
            <td>
              <code>--shadow-lg</code>
            </td>
            <td>
              <code>
                0px 8px 16px oklch(from var(--slate-1000) l c h / 0.15)
              </code>
            </td>
            <td>
              Modals, drawers, slide-over panels. High elevation for overlay
              content.
            </td>
          </tr>
          <tr>
            <td>
              <code>--shadow-xl</code>
            </td>
            <td>
              <code>
                0px 12px 24px oklch(from var(--slate-1000) l c h / 0.20)
              </code>
            </td>
            <td>
              Toast notifications, command palettes. Maximum elevation for
              urgent content.
            </td>
          </tr>
        </tbody>
      </table>
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
          <tr>
            <td>
              <code>--duration-fast</code>
            </td>
            <td>
              <code>100ms</code>
            </td>
            <td>
              Quick feedback. Hover states, toggle switches, checkbox ticks.
            </td>
          </tr>
          <tr>
            <td>
              <code>--duration-normal</code>
            </td>
            <td>
              <code>200ms</code>
            </td>
            <td>
              Standard transitions. Dropdown open, tooltip appear, tab switch.
            </td>
          </tr>
          <tr>
            <td>
              <code>--duration-slow</code>
            </td>
            <td>
              <code>300ms</code>
            </td>
            <td>
              Deliberate emphasis. Modal enter, drawer slide, accordion expand.
            </td>
          </tr>
        </tbody>
      </table>
      <h3>Easing</h3>
      <table className='docs-table'>
        <thead>
          <tr>
            <th>Token</th>
            <th>Value</th>
            <th>Usage</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>--easing-standard</code>
            </td>
            <td>
              <code>cubic-bezier(0.2, 0, 0.38, 0.9)</code>
            </td>
            <td>
              Default for most transitions. Smooth deceleration. Use for
              elements moving within the page.
            </td>
          </tr>
          <tr>
            <td>
              <code>--easing-entrance</code>
            </td>
            <td>
              <code>cubic-bezier(0.0, 0, 0.38, 0.9)</code>
            </td>
            <td>
              Elements entering the viewport. Decelerates into resting position.
              Modals, toasts, slide-ins.
            </td>
          </tr>
          <tr>
            <td>
              <code>--easing-exit</code>
            </td>
            <td>
              <code>cubic-bezier(0.2, 0, 1, 0.9)</code>
            </td>
            <td>
              Elements leaving the viewport. Accelerates out of view. Closing
              modals, dismissing toasts.
            </td>
          </tr>
        </tbody>
      </table>

      <h3>Dark mode shadows</h3>
      <p>
        Dark mode overrides use stronger opacity (0.20-0.40 vs 0.05-0.20).
        Higher elevation surfaces should use lighter backgrounds
        (--color-surface-emphasis) rather than relying solely on shadows.
      </p>

      <h3>Motion pairing</h3>
      <p>
        Combine a duration with an easing: transition: all
        var(--duration-normal) var(--easing-standard). Use --easing-entrance for
        elements appearing, --easing-exit for elements leaving.
      </p>
    </DocPage>
  ),
}
