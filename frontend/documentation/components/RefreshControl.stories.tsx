import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import RefreshControl from 'components/experiments/results/RefreshControl'
import { themeClassNames } from 'components/base/forms/Button'

const themeOptions = Object.keys(themeClassNames) as Array<
  keyof typeof themeClassNames
>

const meta: Meta<typeof RefreshControl> = {
  argTypes: {
    children: {
      control: 'text',
      description: 'Button label. Defaults to "Refresh".',
    },
    disabled: {
      control: 'boolean',
      description: 'Disables the button, preventing interaction.',
    },
    disabledReason: {
      control: 'text',
      description: 'Tooltip explaining why the button is disabled.',
    },
    isRefreshing: {
      control: 'boolean',
      description:
        'Shows a spinner and disables the button while a refresh is in flight. The label stays unchanged.',
    },
    label: {
      control: 'text',
      description:
        'Related message rendered beneath the button — e.g. a retry countdown, an in-progress notice, or an error.',
    },
    theme: {
      control: 'select',
      description: 'Visual variant of the button.',
      options: themeOptions,
      table: { defaultValue: { summary: 'secondary' } },
    },
  },
  args: {
    children: 'Refresh',
    disabled: false,
    isRefreshing: false,
    onRefresh: () => {},
    theme: 'secondary',
  },
  component: RefreshControl,
  parameters: { layout: 'centered' },
  title: 'Experiments/RefreshControl',
}

export default meta

type Story = StoryObj<typeof RefreshControl>

export const Default: Story = {}

export const Refreshing: Story = {
  args: {
    isRefreshing: true,
    label: 'Computing… results will update automatically.',
  },
  parameters: {
    docs: {
      description: {
        story:
          'While a refresh is in flight the button shows a spinner and disables itself, keeping its label. The `label` slot carries the in-progress message.',
      },
    },
  },
}

export const Throttled: Story = {
  args: {
    disabled: true,
    label: 'Computing… retry in 4m 30s',
  },
  parameters: {
    docs: {
      description: {
        story:
          'After hitting the API rate limit (HTTP 429), the caller disables the button and feeds a Retry-After countdown into `label`.',
      },
    },
  },
}

export const Disabled: Story = {
  args: {
    disabled: true,
    disabledReason: 'Refresh is disabled because the experiment is complete.',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Disabled state with a `disabledReason` surfaced as the button tooltip.',
      },
    },
  },
}

export const PrimaryWithError: Story = {
  args: {
    children: 'Refresh results',
    label: (
      <span className='text-danger'>The last results computation failed.</span>
    ),
    theme: 'primary',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Primary theme as used on the experiment results header, with an error message in the `label` slot.',
      },
    },
  },
}
