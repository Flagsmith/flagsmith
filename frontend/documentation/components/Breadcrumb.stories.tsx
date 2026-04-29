import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Breadcrumb from 'components/Breadcrumb'
import { withRouter } from './_decorators'

const meta: Meta = {
  decorators: [withRouter],
  parameters: { layout: 'padded' },
  title: 'Components/Navigation/Breadcrumb',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <Breadcrumb
      items={[
        { title: 'Projects', url: '/projects' },
        { title: 'My Project', url: '/project/1' },
      ]}
      currentPage='Features'
    />
  ),
}

export const SingleLevel: Story = {
  render: () => (
    <Breadcrumb items={[{ title: 'Home', url: '/' }]} currentPage='Settings' />
  ),
}
