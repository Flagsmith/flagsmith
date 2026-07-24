import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import SelectField from 'components/base/forms/SelectField'

const meta: Meta<typeof SelectField> = {
  component: SelectField,
  parameters: { layout: 'padded' },
  title: 'Components/Forms/SelectField',
}
export default meta

type Story = StoryObj<typeof SelectField>

const options = [
  { label: 'Production', value: 'production' },
  { label: 'Staging', value: 'staging' },
  { label: 'Development', value: 'development' },
]

export const Default: Story = {
  render: () => (
    <SelectField title='Environment' options={options} value={options[0]} />
  ),
}

export const Required: Story = {
  render: () => (
    <SelectField
      title='Environment'
      required
      options={options}
      placeholder='Select an environment'
    />
  ),
}

export const WithTooltip: Story = {
  render: () => (
    <SelectField
      title='Environment'
      tooltip='Where this change is applied.'
      options={options}
      value={options[0]}
    />
  ),
}

export const WithError: Story = {
  render: () => (
    <SelectField
      title='Environment'
      options={options}
      error='Select an environment.'
    />
  ),
}

export const Disabled: Story = {
  render: () => (
    <SelectField
      title='Environment'
      options={options}
      value={options[0]}
      isDisabled
    />
  ),
}
