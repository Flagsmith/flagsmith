import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Row from 'components/base/grid/Row'

const meta: Meta = {
  parameters: {
    // Flexbox only, no colour, radius or shadow, so no design token can change
    // how this renders and light/dark are identical. Snapshotting it costs
    // budget for a diff that cannot happen.
    chromatic: { disableSnapshot: true },
    layout: 'padded',
  },
  title: 'Components/Layout/Row',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <Row>
      <div className='p-2 bg-surface-muted'>Item 1</div>
      <div className='p-2 bg-surface-muted'>Item 2</div>
      <div className='p-2 bg-surface-muted'>Item 3</div>
    </Row>
  ),
}

export const SpaceBetween: Story = {
  render: () => (
    <Row space>
      <div className='p-2 bg-surface-muted'>Left</div>
      <div className='p-2 bg-surface-muted'>Right</div>
    </Row>
  ),
}
