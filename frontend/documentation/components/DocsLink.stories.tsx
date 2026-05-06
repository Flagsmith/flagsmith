import React, { ComponentProps } from 'react'
import type { Meta, StoryObj } from 'storybook'

import DocsLink from 'components/DocsLink'

type DocsLinkProps = ComponentProps<typeof DocsLink>

const meta: Meta<DocsLinkProps> = {
  argTypes: {
    children: {
      control: 'text',
      description: 'Link label.',
    },
    href: {
      control: 'text',
      description: 'External docs URL. Always opens in a new tab.',
    },
  },
  args: {
    children: 'View docs',
    href: 'https://docs.flagsmith.com',
  },
  component: DocsLink,
  parameters: {
    docs: {
      description: {
        component:
          'Link to external documentation. Renders as an `<a>` with `target="_blank"` and `rel="noreferrer"` baked in. Replaces the `<Button theme="text" href target="_blank" className="fw-normal">` pattern that was repeated ~17 times across the codebase.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/Navigation/DocsLink',
}
export default meta

type Story = StoryObj<DocsLinkProps>

export const Default: Story = {}

export const Inline: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'DocsLink composes inline with surrounding text — useful for "see the docs" callouts inside paragraphs.',
      },
    },
  },
  render: () => (
    <p className='text-default'>
      Permission groups can be configured at the project level. See{' '}
      <DocsLink href='https://docs.flagsmith.com/system-administration/rbac'>
        the RBAC docs
      </DocsLink>{' '}
      for details.
    </p>
  ),
}
