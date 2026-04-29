import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import { userEvent, within } from 'storybook/test'

import ButtonDropdown from 'components/base/forms/ButtonDropdown'

const meta: Meta = {
  parameters: {
    docs: { story: { height: '260px' } },
    layout: 'centered',
  },
  title: 'Components/ButtonDropdown',
}
export default meta

type Story = StoryObj

const DEMO_ITEMS = [
  { label: 'Edit', onClick: () => {} },
  { label: 'Duplicate', onClick: () => {} },
  { label: 'Delete', onClick: () => {} },
]

export const Default: Story = {
  render: () => (
    <ButtonDropdown dropdownItems={DEMO_ITEMS}>Actions</ButtonDropdown>
  ),
}

export const Open: Story = {
  parameters: {
    chromatic: { delay: 300 },
    docs: {
      description: {
        story:
          'Dropdown menu in its open state. Storybook clicks the chevron toggle in `play` so Chromatic captures the menu.',
      },
    },
  },
  play: async ({ canvasElement }: { canvasElement: HTMLElement }) => {
    const canvas = within(canvasElement)
    const buttons = canvas.getAllByRole('button')
    // Second button is the chevron toggle that opens the menu.
    await userEvent.click(buttons[1])
  },
  render: () => (
    <ButtonDropdown dropdownItems={DEMO_ITEMS}>Actions</ButtonDropdown>
  ),
}
