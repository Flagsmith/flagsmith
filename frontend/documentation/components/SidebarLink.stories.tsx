import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import SidebarLink from 'components/navigation/SidebarLink'
import { withRouter } from './_decorators'

const meta: Meta = {
  decorators: [withRouter],
  parameters: { layout: 'padded' },
  title: 'Components/Navigation/SidebarLink',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <div style={{ width: 240 }}>
      <SidebarLink to='/features' icon='features'>
        Features
      </SidebarLink>
    </div>
  ),
}

export const AllStates: Story = {
  render: () => (
    <div className='d-flex flex-column gap-1' style={{ width: 240 }}>
      <SidebarLink to='/features' icon='features'>
        Features
      </SidebarLink>
      <SidebarLink to='/segments' icon='layers'>
        Segments
      </SidebarLink>
      <SidebarLink to='/settings' icon='setting'>
        Settings
      </SidebarLink>
    </div>
  ),
}
