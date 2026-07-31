import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Link from 'components/base/link'
import Button from 'components/base/forms/Button'
import { Icon } from 'components/icons'
import { withRouter } from './_decorators'

const meta: Meta<typeof Link> = {
  component: Link,
  decorators: [withRouter],
  parameters: { layout: 'padded' },
  title: 'Components/Link',
}
export default meta

type Story = StoryObj<typeof Link>

// An in-app route. No page load, so app state survives the navigation.
export const InApp: Story = {
  render: () => <Link to='/organisations'>Switch organisation</Link>,
}

// Anything outside the app, which needs a real document load.
export const External: Story = {
  render: () => <Link href='https://docs.flagsmith.com'>Read the docs</Link>,
}

// rel is set for you, so a new tab cannot reach back into this one.
export const NewTab: Story = {
  render: () => (
    <Link href='https://docs.flagsmith.com' target='_blank'>
      Read the docs
    </Link>
  ),
}

// The reason vertical-align matters: a link in prose has to sit on the same
// baseline as the text around it.
export const InSentence: Story = {
  render: () => (
    <p>
      Invites are managed from your{' '}
      <Link to='/organisations'>organisation settings</Link>, where you can also
      revoke one that has not been accepted.
    </p>
  ),
}

// Children are laid out with a gap, so an icon needs no spacing of its own.
export const WithIcon: Story = {
  render: () => (
    <Link to='/projects'>
      Continue
      <Icon name='arrow-right' width={16} />
    </Link>
  ),
}

// The distinction the component exists for. The link goes somewhere, the button
// does something, and each carries the element that means that.
export const AlongsideAButton: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-3'>
      <Button onClick={() => undefined}>Create project</Button>
      <Link to='/projects'>View all projects</Link>
    </div>
  ),
}
