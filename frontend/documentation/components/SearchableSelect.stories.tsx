import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import { userEvent, within } from 'storybook/test'

import SearchableSelect, {
  OptionType,
} from 'components/base/select/SearchableSelect'

const PROJECTS: OptionType[] = [
  { label: 'Default Project', value: 'default' },
  { label: 'Marketing Site', value: 'marketing' },
  { label: 'Mobile App', value: 'mobile-app' },
  { label: 'Internal Tools', value: 'internal' },
  { label: 'API Gateway', value: 'api-gateway' },
  { label: 'Payments', value: 'payments' },
]

const GROUPED_OPTIONS = [
  {
    label: 'Frontend',
    options: [
      { label: 'Marketing Site', value: 'marketing' },
      { label: 'Mobile App', value: 'mobile-app' },
    ],
  },
  {
    label: 'Backend',
    options: [
      { label: 'API Gateway', value: 'api-gateway' },
      { label: 'Payments', value: 'payments' },
    ],
  },
]

const meta: Meta<typeof SearchableSelect> = {
  component: SearchableSelect,
  parameters: {
    docs: {
      description: {
        component:
          'Single-select dropdown with type-to-filter search. Supports flat or grouped option lists and an optional clear button. Used for project, role, and feature pickers.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Forms/SearchableSelect',
}
export default meta

type Story = StoryObj<typeof SearchableSelect>

const Interactive = ({
  initial,
  ...rest
}: Omit<React.ComponentProps<typeof SearchableSelect>, 'value'> & {
  initial?: string
}) => {
  const [value, setValue] = useState<string | null>(initial ?? null)
  return (
    <div style={{ width: 360 }}>
      <SearchableSelect
        {...rest}
        value={value}
        onChange={(option) => setValue(option ? option.value : null)}
      />
    </div>
  )
}

export const Default: Story = {
  render: () => (
    <Interactive
      placeholder='Select a project…'
      options={PROJECTS}
      isSearchable
    />
  ),
}

export const WithSelection: Story = {
  render: () => (
    <Interactive
      placeholder='Select a project…'
      options={PROJECTS}
      isSearchable
      initial='mobile-app'
      displayedLabel='Mobile App'
    />
  ),
}

export const Clearable: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Pass `isClearable` to show a clear button next to the value.',
      },
    },
  },
  render: () => (
    <Interactive
      placeholder='Select a project…'
      options={PROJECTS}
      isSearchable
      isClearable
      initial='payments'
      displayedLabel='Payments'
    />
  ),
}

export const GroupedOptions: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Options can be grouped by passing an array of `{ label, options }` instead of a flat list.',
      },
    },
  },
  render: () => (
    <Interactive
      placeholder='Select a project…'
      options={GROUPED_OPTIONS}
      isSearchable
    />
  ),
}

export const Open: Story = {
  parameters: {
    chromatic: { delay: 300 },
    docs: {
      description: { story: 'Dropdown in its open state.' },
      story: { height: '360px' },
    },
  },
  play: async ({ canvasElement }: { canvasElement: HTMLElement }) => {
    const canvas = within(canvasElement)
    await userEvent.click(canvas.getByText('Select a project…'))
  },
  render: () => (
    <Interactive
      placeholder='Select a project…'
      options={PROJECTS}
      isSearchable
    />
  ),
}
