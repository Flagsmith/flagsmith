import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import SettingRow from 'components/SettingRow'
import type { SettingRowProps } from 'components/SettingRow'

const meta: Meta<SettingRowProps> = {
  argTypes: {
    checked: {
      control: 'boolean',
      description: 'Whether the setting is enabled.',
    },
    description: {
      control: 'text',
      description: 'Explanation of what the setting does.',
    },
    disabled: {
      control: 'boolean',
      description: 'Disables the toggle during save operations.',
    },
    title: {
      control: 'text',
      description: 'Setting name displayed as a heading.',
    },
  },
  args: {
    checked: false,
    description: 'Description of what this setting controls.',
    disabled: false,
    title: 'Setting name',
  },
  component: SettingRow,
  parameters: { layout: 'padded' },
  title: 'Patterns/SettingRow',
}

export default meta

type Story = StoryObj<SettingRowProps>

// ---------------------------------------------------------------------------
// Default — interactive playground
// ---------------------------------------------------------------------------

const InteractiveSetting = (args: SettingRowProps) => {
  const [checked, setChecked] = useState(args.checked)
  return <SettingRow {...args} checked={checked} onChange={setChecked} />
}

export const Default: Story = {
  render: (args) => <InteractiveSetting {...args} />,
}

// ---------------------------------------------------------------------------
// Real examples from the codebase
// ---------------------------------------------------------------------------

const PreventFlagDefaultsExample = () => {
  const [checked, setChecked] = useState(false)
  return (
    <SettingRow
      title='Prevent flag defaults'
      description='By default, when creating a feature the value of each environment is set to the initial value and enabled state. Enabling this setting forces the user to create a feature before setting its values per environment.'
      checked={checked}
      onChange={setChecked}
    />
  )
}

export const PreventFlagDefaults: Story = {
  name: 'Prevent flag defaults',
  parameters: {
    docs: {
      description: {
        story:
          'Existing project setting. Prevents defaults from being set across all environments when creating a feature.',
      },
    },
  },
  render: () => <PreventFlagDefaultsExample />,
}

const RequireFeatureOwnershipExample = () => {
  const [checked, setChecked] = useState(true)
  return (
    <SettingRow
      title='Require feature ownership'
      description='When enabled, users must assign at least one owner (user or group) when creating a feature flag. This improves governance by ensuring every feature has a responsible party.'
      checked={checked}
      onChange={setChecked}
    />
  )
}

export const RequireFeatureOwnership: Story = {
  name: 'Require feature ownership',
  parameters: {
    docs: {
      description: {
        story:
          'Proposed setting for issue #4432. When enabled, users must assign at least one owner when creating a feature flag.',
      },
    },
  },
  render: () => <RequireFeatureOwnershipExample />,
}

// ---------------------------------------------------------------------------
// Multiple settings (as they appear in project settings)
// ---------------------------------------------------------------------------

const SettingsGroupExample = () => {
  const [preventDefaults, setPreventDefaults] = useState(false)
  const [caseSensitivity, setCaseSensitivity] = useState(false)
  const [requireOwnership, setRequireOwnership] = useState(true)
  return (
    <div className='d-flex flex-column gap-4'>
      <SettingRow
        title='Prevent flag defaults'
        description='By default, when creating a feature the value of each environment is set to the initial value and enabled state. Enabling this setting forces the user to create a feature before setting its values per environment.'
        checked={preventDefaults}
        onChange={setPreventDefaults}
      />
      <SettingRow
        title='Case sensitive feature names'
        description='By default, feature names are case insensitive. Enabling this setting allows features with names that differ only by case.'
        checked={caseSensitivity}
        onChange={setCaseSensitivity}
      />
      <SettingRow
        title='Require feature ownership'
        description='When enabled, users must assign at least one owner (user or group) when creating a feature flag. This improves governance by ensuring every feature has a responsible party.'
        checked={requireOwnership}
        onChange={setRequireOwnership}
      />
    </div>
  )
}

export const SettingsGroup: Story = {
  name: 'Settings group',
  parameters: {
    docs: {
      description: {
        story:
          'Multiple settings stacked vertically, as they appear in Project Settings → Additional Settings.',
      },
    },
  },
  render: () => <SettingsGroupExample />,
}
