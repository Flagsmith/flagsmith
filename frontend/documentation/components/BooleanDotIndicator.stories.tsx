import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import BooleanDotIndicator from 'components/BooleanDotIndicator'

const meta: Meta<typeof BooleanDotIndicator> = {
  args: { enabled: true },
  component: BooleanDotIndicator,
  parameters: {
    docs: {
      description: {
        component:
          'A small coloured dot signalling an on/off state. Used inline where space is tight — typically inside a tooltip trigger for permission rows or similar binary indicators.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/Data Display/BooleanDotIndicator',
}
export default meta

type Story = StoryObj<typeof BooleanDotIndicator>

export const Enabled: Story = {}

export const Disabled: Story = {
  args: { enabled: false },
}

export const AllStates: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-3'>
      <div className='d-flex align-items-center gap-2'>
        <BooleanDotIndicator enabled /> Enabled
      </div>
      <div className='d-flex align-items-center gap-2'>
        <BooleanDotIndicator enabled={false} /> Disabled
      </div>
    </div>
  ),
}
