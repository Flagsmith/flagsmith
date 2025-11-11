import type { Meta, StoryObj } from '@storybook/react'
import { MultiSelect } from '../../../web/components/base/select/multi-select/MultiSelect'
import React, { useState } from 'react'

const meta: Meta<typeof MultiSelect> = {
  title: 'Components/MultiSelect',
  component: MultiSelect,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof MultiSelect>

// Wrapper component to handle state
const MultiSelectWrapper = (args: any) => {
  const [selectedValues, setSelectedValues] = useState<string[]>(
    args.selectedValues || []
  )

  return (
    <div style={{ width: '400px' }}>
      <MultiSelect
        {...args}
        selectedValues={selectedValues}
        onSelectionChange={setSelectedValues}
      />
    </div>
  )
}

// Basic example with simple options
export const Default: Story = {
  render: (args) => <MultiSelectWrapper {...args} />,
  args: {
    options: [
      { label: 'Option 1', value: 'option1' },
      { label: 'Option 2', value: 'option2' },
      { label: 'Option 3', value: 'option3' },
      { label: 'Option 4', value: 'option4' },
      { label: 'Option 5', value: 'option5' },
    ],
    placeholder: 'Select options...',
    selectedValues: [],
    hideSelectedOptions: true,
  },
}

// With label
export const WithLabel: Story = {
  render: (args) => <MultiSelectWrapper {...args} />,
  args: {
    ...Default.args,
    label: 'Choose your options',
  },
}

// With colors
export const WithColors: Story = {
  render: (args) => <MultiSelectWrapper {...args} />,
  args: {
    options: [
      { label: 'Red', value: 'red' },
      { label: 'Green', value: 'green' },
      { label: 'Blue', value: 'blue' },
      { label: 'Yellow', value: 'yellow' },
      { label: 'Purple', value: 'purple' },
    ],
    colorMap: new Map([
      ['red', '#EF4444'],
      ['green', '#10B981'],
      ['blue', '#3B82F6'],
      ['yellow', '#F59E0B'],
      ['purple', '#8B5CF6'],
    ]),
    placeholder: 'Select colors...',
    selectedValues: [],
    hideSelectedOptions: true,
  },
}

// Pre-selected values
export const WithPreselectedValues: Story = {
  render: (args) => <MultiSelectWrapper {...args} />,
  args: {
    ...WithColors.args,
    selectedValues: ['red', 'blue'],
  },
}

// Disabled state
export const Disabled: Story = {
  render: (args) => <MultiSelectWrapper {...args} />,
  args: {
    ...Default.args,
    disabled: true,
    selectedValues: ['option1', 'option2'],
  },
}

// Small size
export const SmallSize: Story = {
  render: (args) => <MultiSelectWrapper {...args} />,
  args: {
    ...Default.args,
    size: 'small',
    label: 'Small size select',
  },
}

// Large size
export const LargeSize: Story = {
  render: (args) => <MultiSelectWrapper {...args} />,
  args: {
    ...Default.args,
    size: 'large',
    label: 'Large size select',
  },
}

// Show selected options in dropdown
export const ShowSelectedOptions: Story = {
  render: (args) => <MultiSelectWrapper {...args} />,
  args: {
    ...Default.args,
    hideSelectedOptions: false,
    selectedValues: ['option1', 'option2'],
  },
}

// Inline display
export const InlineDisplay: Story = {
  render: (args) => <MultiSelectWrapper {...args} />,
  args: {
    ...Default.args,
    inline: true,
    selectedValues: ['option1', 'option2', 'option3'],
  },
}

// Many options
export const ManyOptions: Story = {
  render: (args) => <MultiSelectWrapper {...args} />,
  args: {
    options: Array.from({ length: 50 }, (_, i) => ({
      label: `Option ${i + 1}`,
      value: `option${i + 1}`,
    })),
    placeholder: 'Search and select...',
    selectedValues: [],
    label: 'Select from many options',
  },
}

// Long option labels
export const LongLabels: Story = {
  render: (args) => <MultiSelectWrapper {...args} />,
  args: {
    options: [
      {
        label: 'This is a very long option label that might overflow',
        value: 'long1',
      },
      {
        label: 'Another extremely long label to test text overflow behavior',
        value: 'long2',
      },
      {
        label: 'Short label',
        value: 'short',
      },
    ],
    placeholder: 'Select options...',
    selectedValues: [],
  },
}
