import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import { BareButton, BareButtonProps } from 'components/base/forms/BareButton'
import { Icon } from 'components/icons'

const meta: Meta<BareButtonProps> = {
  argTypes: {
    children: {
      control: 'text',
      description: 'Content rendered inside the bare button.',
    },
    disabled: {
      control: 'boolean',
      description:
        'Disables the button — native `disabled` attribute, no manual ARIA needed.',
    },
  },
  args: {
    children: 'Click me',
    disabled: false,
  },
  component: BareButton,
  parameters: { layout: 'centered' },
  title: 'Components/Forms/BareButton',
}

export default meta

type Story = StoryObj<BareButtonProps>

export const Default: Story = {}

export const Disabled: Story = {
  args: { disabled: true },
  parameters: {
    docs: {
      description: {
        story:
          'A disabled `BareButton` is non-interactive and removes the pointer cursor automatically.',
      },
    },
  },
}

export const AsSelectableCard: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Demonstrates how `BareButton` can wrap a card-like surface. All keyboard, focus and disabled semantics come for free.',
      },
    },
  },
  render: () => (
    <BareButton
      style={{
        border: '2px solid var(--color-border-default)',
        borderRadius: 'var(--radius-xl)',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
        padding: 16,
        textAlign: 'left',
        width: 240,
      }}
      onClick={() => alert('Card clicked')}
    >
      <strong>Selectable card</strong>
      <span style={{ fontSize: 'var(--font-caption-size)' }}>
        Tap or press Enter / Space to activate.
      </span>
    </BareButton>
  ),
}

export const AsChipDelete: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Demonstrates replacing a `<span role="button">` chip-delete icon with a semantic `BareButton`.',
      },
    },
  },
  render: () => (
    <span
      className='chip'
      style={{ alignItems: 'center', display: 'inline-flex', gap: 4 }}
    >
      my-tag
      <BareButton aria-label='Remove tag' onClick={() => alert('Deleted')}>
        <Icon name='close' width={16} height={16} fill='currentColor' />
      </BareButton>
    </span>
  ),
}
