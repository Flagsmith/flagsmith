import type { Meta, StoryObj } from 'storybook'
import Banner, { BannerProps } from 'components/Banner'
import { Button } from 'components/base/forms/Button'

const meta: Meta<BannerProps> = {
  component: Banner,
  parameters: { chromatic: { disableSnapshot: false }, layout: 'padded' },
  title: 'Components/Banner',
}

export default meta

type Story = StoryObj<BannerProps>

export const Info: Story = {
  args: {
    children: 'Your changes will apply on the next deployment.',
    variant: 'info',
  },
}

export const Success: Story = {
  args: { children: 'Webhook saved.', variant: 'success' },
}

export const Warning: Story = {
  args: {
    children: 'You have used 41.2K of your 50K allowed requests.',
    variant: 'warning',
  },
}

// Only danger carries role='alert', so a screen reader is interrupted by the
// states worth interrupting for and left alone by the rest.
export const Danger: Story = {
  args: {
    children: 'Your organisation has exceeded its plan limit.',
    variant: 'danger',
  },
}

export const WithAnAction: Story = {
  args: {
    children: (
      <>
        <span className='flex-fill'>
          Your organisation has exceeded its plan limit.
        </span>
        <Button className='flex-shrink-0'>Upgrade plan</Button>
      </>
    ),
    variant: 'danger',
  },
}

// Long bodies wrap against the icon rather than under it.
export const Wrapping: Story = {
  args: {
    children:
      'We could not fetch usage for this period. This is usually temporary, ' +
      'so try again in a moment. If it keeps happening, get in touch with ' +
      'support and quote your organisation ID.',
    variant: 'danger',
  },
}
