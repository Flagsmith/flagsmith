import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import { userEvent, within } from 'storybook/test'

import OverflowNav from 'components/navigation/OverflowNav'
import NavSubLink from 'components/navigation/NavSubLink'
import Icon from 'components/icons/Icon'
import { withRouter } from './_decorators'

const meta: Meta = {
  decorators: [withRouter],
  parameters: {
    docs: {
      description: {
        component:
          'Horizontal navigation bar that gracefully collapses extra items into an overflow menu when the container is too narrow. Wrap `NavSubLink` items inside it.',
      },
      story: { height: '320px' },
    },
    layout: 'padded',
  },
  title: 'Components/Navigation/OverflowNav',
}
export default meta

type Story = StoryObj

const NAV_ITEMS = (
  <>
    <NavSubLink to='/project/1/features' icon={<Icon name='features' />}>
      Features
    </NavSubLink>
    <NavSubLink to='/project/1/segments' icon={<Icon name='layers' />}>
      Segments
    </NavSubLink>
    <NavSubLink to='/project/1/audit-log' icon={<Icon name='clock' />}>
      Audit Log
    </NavSubLink>
    <NavSubLink to='/project/1/change-requests' icon={<Icon name='request' />}>
      Change Requests
    </NavSubLink>
    <NavSubLink to='/project/1/settings' icon={<Icon name='setting' />}>
      Settings
    </NavSubLink>
  </>
)

export const ProjectNavbar: Story = {
  render: () => (
    <OverflowNav
      gap={3}
      containerClassName='px-2 pb-1 bg-faint'
      className='py-0 d-flex'
    >
      {NAV_ITEMS}
    </OverflowNav>
  ),
}

export const WithOverflow: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'When items exceed the container width an overflow menu is shown with the remaining items. Forced here via the `force` prop so it always renders the overflow trigger.',
      },
    },
  },
  render: () => (
    <OverflowNav
      force
      gap={3}
      containerClassName='px-2 pb-1 bg-faint'
      className='py-0 d-flex'
    >
      {NAV_ITEMS}
    </OverflowNav>
  ),
}

export const OverflowOpen: Story = {
  parameters: {
    chromatic: { delay: 300 },
    docs: {
      description: {
        story:
          'Overflow menu in its open state. Storybook clicks the overflow trigger in `play` so Chromatic captures the popover.',
      },
    },
  },
  play: async ({ canvasElement }: { canvasElement: HTMLElement }) => {
    const canvas = within(canvasElement)
    // The only <button> in the rendered nav is the overflow trigger;
    // NavSubLink items render as anchors.
    const triggers = canvas.getAllByRole('button')
    await userEvent.click(triggers[triggers.length - 1])
  },
  render: () => (
    <OverflowNav
      force
      gap={3}
      containerClassName='px-2 pb-1 bg-faint'
      className='py-0 d-flex'
    >
      {NAV_ITEMS}
    </OverflowNav>
  ),
}
