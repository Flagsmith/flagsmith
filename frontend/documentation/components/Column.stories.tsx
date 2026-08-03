import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Column from 'components/base/grid/Column'

const meta: Meta = {
  parameters: {
    // Flexbox only, no colour, radius or shadow, so no design token can change
    // how this renders and light/dark are identical. Snapshotting it costs
    // budget for a diff that cannot happen.
    chromatic: { disableSnapshot: true },
    layout: 'padded',
  },
  title: 'Components/Layout/Column',
}
export default meta

type Story = StoryObj

const Block: React.FC<{ label: string }> = ({ label }) => (
  <div className='bg-surface-subtle rounded-1 p-3'>{label}</div>
)

export const Default: Story = {
  render: () => (
    <Column className='gap-2' style={{ width: 240 }}>
      <Block label='First' />
      <Block label='Second' />
      <Block label='Third' />
    </Column>
  ),
}
