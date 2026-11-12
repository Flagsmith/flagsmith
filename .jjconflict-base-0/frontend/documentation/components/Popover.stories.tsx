import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import { screen, userEvent, within } from 'storybook/test'

import Popover from 'components/base/Popover'
import Button from 'components/base/forms/Button'

const meta: Meta<typeof Popover> = {
  component: Popover,
  parameters: {
    docs: { story: { height: '240px' } },
    layout: 'centered',
  },
  title: 'Components/Modals/Popover',
}
export default meta

type Story = StoryObj<typeof Popover>

const renderPopover = () => (
  <Popover
    aria-label='Sort'
    renderTrigger={(props) => (
      <Button theme='secondary' {...props}>
        Sort by
      </Button>
    )}
  >
    {(close) => (
      <div className='d-flex flex-column p-2'>
        <Button theme='text' onClick={close}>
          Name
        </Button>
        <Button theme='text' onClick={close}>
          Last updated
        </Button>
      </div>
    )}
  </Popover>
)

export const Default: Story = {
  render: renderPopover,
}

export const Open: Story = {
  parameters: {
    chromatic: { delay: 300 },
  },
  play: async ({ canvasElement }: { canvasElement: HTMLElement }) => {
    const canvas = within(canvasElement)
    await userEvent.click(canvas.getByRole('button', { name: 'Sort by' }))
    await screen.findByRole('dialog', { name: 'Sort' })
  },
  render: renderPopover,
}
