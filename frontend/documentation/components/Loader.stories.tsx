import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Loader from 'components/Loader'

const meta: Meta<typeof Loader> = {
  argTypes: {
    fill: { control: 'color' },
  },
  args: {
    fill: 'currentColor',
    height: '40px',
    width: '40px',
  },
  component: Loader,
  parameters: {
    // SVG animateTransform spins continuously; Chromatic snapshots at
    // random rotation angles and reports false-positive diffs on every
    // build. Skip visual snapshots for this component.
    chromatic: { disableSnapshot: true },
    layout: 'centered',
  },
  title: 'Components/Feedback/Loader',
}
export default meta

type Story = StoryObj<typeof Loader>

export const Default: Story = {}

export const Small: Story = {
  args: { height: '20px', width: '20px' },
}

export const Sizes: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-4'>
      <Loader width='16px' height='16px' />
      <Loader width='24px' height='24px' />
      <Loader width='40px' height='40px' />
      <Loader width='64px' height='64px' />
    </div>
  ),
}
