import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Banner from 'components/Banner'
import type { BannerProps } from 'components/Banner'
import { Button } from 'components/base/forms/Button'

const meta: Meta<BannerProps> = {
  argTypes: {
    children: {
      control: 'text',
      description:
        'Banner message content. Can include a CTA button as a child.',
    },
    variant: {
      control: 'select',
      description: 'Feedback colour variant.',
      options: ['success', 'warning', 'danger', 'info'],
    },
  },
  args: {
    children: 'This is a banner message.',
    variant: 'info',
  },
  component: Banner,
  parameters: { layout: 'padded' },
  title: 'Components/Banner',
}

export default meta

type Story = StoryObj<BannerProps>

// ---------------------------------------------------------------------------
// Default — interactive playground
// ---------------------------------------------------------------------------

export const Default: Story = {}

// ---------------------------------------------------------------------------
// Individual variants
// ---------------------------------------------------------------------------

export const Success: Story = {
  args: {
    children: 'Your changes have been saved successfully.',
    variant: 'success',
  },
  parameters: {
    docs: {
      description: {
        story: 'Use `success` for confirming a completed action.',
      },
    },
  },
}

export const Warning: Story = {
  args: {
    children: 'Your trial is ending in 3 days.',
    variant: 'warning',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Use `warning` for cautionary messages that need attention but are not critical.',
      },
    },
  },
}

export const Danger: Story = {
  args: {
    children: 'Your API key has been revoked.',
    variant: 'danger',
  },
  parameters: {
    docs: {
      description: {
        story: 'Use `danger` for errors or critical issues.',
      },
    },
  },
}

export const Info: Story = {
  args: {
    children: 'A new version of Flagsmith is available.',
    variant: 'info',
  },
  parameters: {
    docs: {
      description: {
        story: 'Use `info` for neutral informational messages.',
      },
    },
  },
}

// ---------------------------------------------------------------------------
// With CTA (passed as children)
// ---------------------------------------------------------------------------

export const WithCTA: Story = {
  name: 'With CTA button',
  parameters: {
    docs: {
      description: {
        story:
          'Add a CTA by passing a `Button` as part of `children`. This keeps the Banner API simple — the banner renders whatever you give it.',
      },
    },
  },
  render: () => (
    <Banner variant='warning'>
      <span className='flex-fill'>Your trial is ending in 3 days.</span>
      <Button className='btn ml-3' size='small' theme='primary'>
        Upgrade Plan
      </Button>
    </Banner>
  ),
}

export const DangerWithCTA: Story = {
  name: 'Danger with CTA',
  parameters: {
    docs: {
      description: {
        story:
          'For danger banners, use `theme="danger"` on the CTA button for visual consistency.',
      },
    },
  },
  render: () => (
    <Banner variant='danger'>
      <span className='flex-fill'>Your API key has been revoked.</span>
      <Button className='btn ml-3' size='small' theme='danger'>
        Generate New Key
      </Button>
    </Banner>
  ),
}

// ---------------------------------------------------------------------------
// All variants
// ---------------------------------------------------------------------------

export const AllVariants: Story = {
  name: 'All variants',
  parameters: {
    docs: {
      description: {
        story:
          'All four banner variants. Each has a default icon that matches the variant. Banners are persistent — not closable or dismissable.',
      },
    },
  },
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Banner variant='success'>
        Your changes have been saved successfully.
      </Banner>
      <Banner variant='warning'>
        <span className='flex-fill'>Your trial is ending in 3 days.</span>
        <Button className='btn ml-3' size='small' theme='primary'>
          Upgrade Plan
        </Button>
      </Banner>
      <Banner variant='danger'>
        <span className='flex-fill'>Your API key has been revoked.</span>
        <Button className='btn ml-3' size='small' theme='danger'>
          Generate New Key
        </Button>
      </Banner>
      <Banner variant='info'>A new version of Flagsmith is available.</Banner>
    </div>
  ),
}
