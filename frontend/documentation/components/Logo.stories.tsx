import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Logo from 'components/Logo'

const meta: Meta<typeof Logo> = {
  argTypes: {
    size: { control: { max: 512, min: 16, step: 8, type: 'range' } },
  },
  args: { size: 256 },
  component: Logo,
  parameters: { layout: 'centered' },
  title: 'Components/Data Display/Logo',
}
export default meta

type Story = StoryObj<typeof Logo>

export const Default: Story = {}

export const Small: Story = {
  args: { size: 128 },
}

export const Sizes: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-4'>
      <Logo size={64} />
      <Logo size={128} />
      <Logo size={256} />
    </div>
  ),
}
