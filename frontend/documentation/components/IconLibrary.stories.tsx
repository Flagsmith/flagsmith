import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import * as icons from 'components/icons'
import type { IconComponent } from 'components/icons'

// eslint-disable-next-line @dword-design/import-alias/prefer-alias
import '../docs.scss'

const meta: Meta = {
  parameters: { chromatic: { disableSnapshot: false }, layout: 'padded' },
  title: 'Components/Icon library',
}
export default meta

const ICONS = Object.entries(icons).filter(
  (entry): entry is [string, IconComponent] =>
    entry[0] !== 'Icon' && typeof entry[1] === 'function',
)

const SIZES = [14, 16, 20, 24]

export const Catalogue: StoryObj = {
  render: () => (
    <div className='icon-catalogue__grid'>
      {ICONS.map(([name, Svg]) => (
        <div className='icon-catalogue__card' key={name}>
          <Svg />
          <code>{name}</code>
        </div>
      ))}
    </div>
  ),
}

// The 1.5px stroke scales with the icon, so small sizes draw thinner lines
export const Sizes: StoryObj = {
  render: () => (
    <table>
      <tbody>
        {ICONS.map(([name, Svg]) => (
          <tr key={name}>
            <td>
              <code>{name}</code>
            </td>
            {SIZES.map((size) => (
              <td className='px-3 py-1' key={size}>
                <Svg width={size} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  ),
}
