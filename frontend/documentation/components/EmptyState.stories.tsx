import React, { ComponentProps } from 'react'
import type { Meta, StoryObj } from 'storybook'

import EmptyState from 'components/EmptyState'
import Button from 'components/base/forms/Button'

type EmptyStateProps = ComponentProps<typeof EmptyState>

const meta: Meta<EmptyStateProps> = {
  argTypes: {
    description: {
      control: 'text',
      description: 'Supporting copy below the title.',
    },
    docsLabel: {
      control: 'text',
      description: 'Link label when `docsUrl` is set.',
    },
    docsUrl: {
      control: 'text',
      description: 'Optional docs link rendered below the description.',
    },
    icon: {
      control: 'select',
      description:
        'Icon name from the design system. A representative subset is exposed here; the component accepts any `IconName`.',
      options: [
        'features',
        'people',
        'flask',
        'info',
        'search',
        'setting',
        'shield',
        'bar-chart',
        'pie-chart',
        'bell',
      ],
    },
    iconColour: {
      control: 'color',
      description:
        'Icon fill colour. Defaults to a neutral grey when not provided.',
    },
    title: {
      control: 'text',
      description: 'Headline shown to the user.',
    },
  },
  args: {
    description: 'Create your first feature flag to get started.',
    icon: 'features',
    title: 'No features yet',
  },
  component: EmptyState,
  parameters: { layout: 'padded' },
  title: 'Components/Feedback/EmptyState',
}
export default meta

type Story = StoryObj<EmptyStateProps>

// ---------------------------------------------------------------------------
// Default — interactive playground (controls-driven)
// ---------------------------------------------------------------------------

export const Default: Story = {}

// ---------------------------------------------------------------------------
// Variants — deterministic snapshots
// ---------------------------------------------------------------------------

export const WithAction: Story = {
  args: {
    description: 'Segments let you target specific users.',
    icon: 'people',
    title: 'No segments found',
  },
  render: (args: EmptyStateProps) => (
    <EmptyState
      {...args}
      action={<Button theme='primary'>Create segment</Button>}
    />
  ),
}

export const WithDocsLink: Story = {
  args: {
    description: 'Read the docs to learn how to set up your first project.',
    docsLabel: 'View docs',
    docsUrl: 'https://docs.flagsmith.com',
    icon: 'info',
    title: 'No projects yet',
  },
}
