import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import {
  Button,
  themeClassNames,
  sizeClassNames,
} from 'components/base/forms/Button'
import type { ButtonType } from 'components/base/forms/Button'
import { Icon } from 'components/icons'

const themeOptions = Object.keys(themeClassNames) as Array<
  keyof typeof themeClassNames
>
const sizeOptions = Object.keys(sizeClassNames) as Array<
  keyof typeof sizeClassNames
>

const meta: Meta<ButtonType> = {
  argTypes: {
    children: {
      control: 'text',
      description: 'Button label content. Compose icons via `<Icon>` children.',
    },
    disabled: {
      control: 'boolean',
      description: 'Disables the button, preventing interaction.',
    },
    size: {
      control: 'select',
      description: 'Size of the button.',
      options: sizeOptions,
      table: { defaultValue: { summary: 'default' } },
    },
    theme: {
      control: 'select',
      description: 'Visual variant of the button.',
      options: themeOptions,
      table: { defaultValue: { summary: 'primary' } },
    },
  },
  args: {
    children: 'Button',
    disabled: false,
    size: 'default',
    theme: 'primary',
  },
  component: Button,
  parameters: { layout: 'centered' },
  title: 'Components/Button',
}

export default meta

type Story = StoryObj<ButtonType>

export const Default: Story = {}

export const Variants: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'All available button themes. Use `primary` for main actions, `secondary` for alternatives, `outline` for low-emphasis actions, `danger` for destructive actions, and `success` for positive confirmations.',
      },
    },
  },
  render: () => (
    <div className='d-flex align-items-center flex-wrap gap-2'>
      <Button theme='primary'>Primary</Button>
      <Button theme='secondary'>Secondary</Button>
      <Button theme='outline'>Outline</Button>
      <Button theme='danger'>Danger</Button>
      <Button theme='success'>Success</Button>
      <Button theme='tertiary'>Tertiary</Button>
      <Button theme='text'>Text</Button>
      <Button theme='icon'>
        <Icon name='copy' />
      </Button>
    </div>
  ),
}

export const Sizes: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Button sizes from large to extra-extra small.',
      },
    },
  },
  render: () => (
    <div className='d-flex align-items-center flex-wrap gap-2'>
      <Button size='large'>Large</Button>
      <Button size='default'>Default</Button>
      <Button size='small'>Small</Button>
      <Button size='xSmall'>Extra Small</Button>
      <Button size='xxSmall'>XX Small</Button>
    </div>
  ),
}

export const Disabled: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Disabled buttons are non-interactive and visually muted.',
      },
    },
  },
  render: () => (
    <div className='d-flex align-items-center flex-wrap gap-2'>
      <Button theme='primary' disabled>
        Primary
      </Button>
      <Button theme='secondary' disabled>
        Secondary
      </Button>
      <Button theme='danger' disabled>
        Danger
      </Button>
      <Button theme='outline' disabled>
        Outline
      </Button>
    </div>
  ),
}

export const WithIcons: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Icons compose via children — pass `<Icon>` JSX directly alongside the label. Button handles icon+label spacing internally.',
      },
    },
  },
  render: () => (
    <div className='d-flex align-items-center flex-wrap gap-2'>
      <Button theme='primary'>
        <Icon name='plus' />
        Add Item
      </Button>
      <Button theme='danger'>
        <Icon name='trash-2' />
        Delete
      </Button>
      <Button theme='outline'>
        Next
        <Icon name='chevron-right' />
      </Button>
    </div>
  ),
}
