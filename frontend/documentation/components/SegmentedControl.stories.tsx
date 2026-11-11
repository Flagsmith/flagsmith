import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import SegmentedControl, {
  SegmentedControlProps,
} from 'components/base/SegmentedControl'

const SCOPE = [
  { label: 'Everything', value: 'all' },
  { label: 'Organisation', value: 'organisation' },
  { label: 'Project', value: 'project' },
]

const Interactive = (args: SegmentedControlProps<string>) => {
  const [value, setValue] = useState(args.value)
  return <SegmentedControl {...args} value={value} onChange={setValue} />
}

const meta: Meta<typeof SegmentedControl<string>> = {
  args: { 'aria-label': 'Scope', options: SCOPE, value: 'all' },
  component: SegmentedControl,
  parameters: {
    docs: {
      description: {
        component:
          'One choice from two to five, all visible. A radio group: Tab reaches the checked option and arrow keys move the selection. The indicator slides between options and stays still under reduced motion.',
      },
    },
    layout: 'centered',
  },
  render: (args) => <Interactive {...args} />,
  title: 'Components/Forms/SegmentedControl',
}
export default meta

type Story = StoryObj<typeof SegmentedControl<string>>

export const Default: Story = {}

export const SecondSelected: Story = { args: { value: 'organisation' } }

export const TwoOptions: Story = {
  args: {
    'aria-label': 'Theme',
    options: [
      { label: 'Light', value: 'light' },
      { label: 'Dark', value: 'dark' },
    ],
    value: 'light',
  },
}
