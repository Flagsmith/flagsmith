import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import { screen, userEvent, within } from 'storybook/test'

import DropdownMenu from 'components/base/DropdownMenu'

const meta: Meta = {
  parameters: {
    docs: { story: { height: '260px' } },
    layout: 'centered',
  },
  title: 'Components/Data Display/DropdownMenu',
}
export default meta

type Story = StoryObj

const DEMO_ITEMS = [
  { label: 'Edit', onClick: () => {} },
  { label: 'Duplicate', onClick: () => {} },
  { label: 'Archive', onClick: () => {} },
  { label: 'Delete', onClick: () => {} },
]

export const Default: Story = {
  render: () => <DropdownMenu items={DEMO_ITEMS} />,
}

export const Open: Story = {
  parameters: {
    chromatic: { delay: 300 },
    docs: {
      description: {
        story:
          'Menu in its open state. Storybook clicks the trigger in `play`; the menu portals into `document.body`, so it is queried via `screen` rather than the local canvas.',
      },
    },
  },
  play: async ({ canvasElement }: { canvasElement: HTMLElement }) => {
    const canvas = within(canvasElement)
    await userEvent.click(canvas.getByRole('button'))
    await screen.findByText('Edit')
  },
  render: () => <DropdownMenu items={DEMO_ITEMS} />,
}
