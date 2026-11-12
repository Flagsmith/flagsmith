import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import VCSProviderTag from 'components/tags/VCSProviderTag'
import { VCSProvider } from 'common/types/responses'

const meta: Meta<typeof VCSProviderTag> = {
  args: {
    count: 3,
    vcsProvider: VCSProvider.GITHUB,
  },
  component: VCSProviderTag,
  parameters: { layout: 'centered' },
  title: 'Components/Data Display/VCSProviderTag',
}
export default meta

type Story = StoryObj<typeof VCSProviderTag>

export const GitHub: Story = {}

export const Warning: Story = {
  args: { count: 0, isWarning: true },
}

export const AllProviders: Story = {
  render: () => (
    <div className='d-flex gap-2'>
      <VCSProviderTag vcsProvider={VCSProvider.GITHUB} count={3} />
      <VCSProviderTag vcsProvider={VCSProvider.GITLAB} count={1} />
      <VCSProviderTag vcsProvider={VCSProvider.BITBUCKET} count={2} />
    </div>
  ),
}
