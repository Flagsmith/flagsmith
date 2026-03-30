import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Switch from 'components/Switch'
import type { SwitchProps } from 'components/Switch'

const meta: Meta<SwitchProps> = {
  argTypes: {
    checked: {
      control: 'boolean',
      description: 'Whether the switch is on or off.',
    },
    disabled: {
      control: 'boolean',
      description: 'Disables the switch, preventing interaction.',
    },
  },
  args: {
    checked: false,
    disabled: false,
  },
  component: Switch,
  parameters: { layout: 'centered' },
  title: 'Components/Switch',
}

export default meta

type Story = StoryObj<SwitchProps>

// ---------------------------------------------------------------------------
// Default — interactive
// ---------------------------------------------------------------------------

const InteractiveSwitch = () => {
  const [checked, setChecked] = useState(false)
  return <Switch checked={checked} onChange={setChecked} />
}

export const Default: Story = {
  render: () => <InteractiveSwitch />,
}

// ---------------------------------------------------------------------------
// States
// ---------------------------------------------------------------------------

export const States: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Switch in all visual states: off, on, and disabled.',
      },
    },
  },
  render: () => (
    <div style={{ alignItems: 'center', display: 'flex', gap: 24 }}>
      <div style={{ alignItems: 'center', display: 'flex', gap: 8 }}>
        <Switch checked={false} />
        <span>Off</span>
      </div>
      <div style={{ alignItems: 'center', display: 'flex', gap: 8 }}>
        <Switch checked={true} />
        <span>On</span>
      </div>
      <div style={{ alignItems: 'center', display: 'flex', gap: 8 }}>
        <Switch checked={false} disabled />
        <span>Disabled</span>
      </div>
    </div>
  ),
}
