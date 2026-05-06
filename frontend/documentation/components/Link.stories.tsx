import React, { ComponentProps } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Link from 'components/Link'
import Icon from 'components/icons/Icon'

type LinkProps = ComponentProps<typeof Link>

const meta: Meta<LinkProps> = {
  argTypes: {
    children: {
      control: 'text',
      description: 'Link content. Composes naturally with text and icons.',
    },
    external: {
      control: 'boolean',
      description:
        'Forces or suppresses external behaviour. Defaults to auto-detect: `true` for `http(s)://` URLs, `false` otherwise.',
    },
    href: {
      control: 'text',
      description: 'Link target. Internal paths or external URLs.',
    },
    noUnderline: {
      control: 'boolean',
      description: 'Drops the hover underline.',
    },
  },
  args: {
    children: 'View docs',
    href: 'https://docs.flagsmith.com',
  },
  component: Link,
  parameters: {
    docs: {
      description: {
        component:
          'Anchor primitive. Children-only — icons compose via JSX, no `iconLeft`/`iconRight` props. External-vs-internal behaviour auto-detects from the URL.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/Navigation/Link',
}
export default meta

type Story = StoryObj<LinkProps>

export const Default: Story = {}

export const Internal: Story = {
  args: {
    children: 'Go to features',
    href: '/features',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Internal route — does NOT add `target="_blank"` (auto-detected from non-`http(s)://` href).',
      },
    },
  },
}

export const Inline: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Inline composition with surrounding text — typical "see the docs" callout.',
      },
    },
  },
  render: () => (
    <p className='text-default'>
      Permission groups can be configured at the project level. See{' '}
      <Link href='https://docs.flagsmith.com/system-administration/rbac'>
        the RBAC docs
      </Link>{' '}
      for details.
    </p>
  ),
}

export const WithIcon: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Icon + label via children composition — no `iconLeft`/`iconRight` props. Spacing handled by the link wrapper.',
      },
    },
  },
  render: () => (
    <Link href='https://docs.flagsmith.com'>
      <Icon name='open-external-link' width={14} /> Open in new tab
    </Link>
  ),
}

export const NoUnderline: Story = {
  args: {
    noUnderline: true,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Hides the hover underline — useful for links inside dense layouts where the underline is too noisy.',
      },
    },
  },
}
