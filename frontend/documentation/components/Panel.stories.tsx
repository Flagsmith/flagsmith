import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Panel from 'components/base/grid/Panel'

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'Boxed content section with an optional title and action slot in the header. Use it to group related content blocks on a page; for plain content surfaces without a header, prefer `Card`.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Patterns/Panel',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <Panel title='Panel title'>
      <p className='mb-0'>Panel content goes here.</p>
    </Panel>
  ),
}

export const WithAction: Story = {
  render: () => (
    <Panel title='Features' action={<a href='#'>View all</a>}>
      <p className='mb-0'>Feature list content.</p>
    </Panel>
  ),
}

export const NoTitle: Story = {
  render: () => (
    <Panel>
      <p className='mb-0'>Panel without a title header.</p>
    </Panel>
  ),
}
