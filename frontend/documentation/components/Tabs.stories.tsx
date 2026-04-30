import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import { withRouter } from './_decorators'

const meta: Meta = {
  decorators: [withRouter],
  parameters: {
    docs: {
      description: {
        component:
          'In-page tabs for splitting content into sections (e.g. Settings ▸ General | Permissions | Webhooks). Compose with `TabItem` children. Use the default theme for primary navigation between content areas; use `theme="pill"` for compact secondary switching.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Navigation/Tabs',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <Tabs uncontrolled>
      <TabItem tabLabel='Features'>
        <p className='mt-3'>Features tab content</p>
      </TabItem>
      <TabItem tabLabel='Segments'>
        <p className='mt-3'>Segments tab content</p>
      </TabItem>
      <TabItem tabLabel='Settings'>
        <p className='mt-3'>Settings tab content</p>
      </TabItem>
    </Tabs>
  ),
}

export const PillTheme: Story = {
  render: () => (
    <Tabs theme='pill' uncontrolled>
      <TabItem tabLabel='Overview'>
        <p className='mt-3'>Overview content</p>
      </TabItem>
      <TabItem tabLabel='Activity'>
        <p className='mt-3'>Activity content</p>
      </TabItem>
    </Tabs>
  ),
}
