import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import {
  MultiSelect,
  MultiSelectOption,
} from 'components/base/select/multi-select/MultiSelect'
import { colorChart1, colorChart3, colorChart4 } from 'common/theme/tokens'

const FRUITS: MultiSelectOption[] = [
  { label: 'Apple', value: 'apple' },
  { label: 'Banana', value: 'banana' },
  { label: 'Cherry', value: 'cherry' },
  { label: 'Mango', value: 'mango' },
  { label: 'Pineapple', value: 'pineapple' },
]

const meta: Meta<typeof MultiSelect> = {
  component: MultiSelect,
  parameters: {
    docs: {
      description: {
        component:
          'Multi-select dropdown for picking several values at once. Pass a `colorMap` to render coloured swatches next to each option and selected chip — useful for tag and environment pickers.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Forms/MultiSelect',
}
export default meta

type Story = StoryObj<typeof MultiSelect>

const Interactive = (
  args: Omit<
    React.ComponentProps<typeof MultiSelect>,
    'selectedValues' | 'onSelectionChange'
  > & { initial?: string[] },
) => {
  const { initial = [], ...rest } = args
  const [selected, setSelected] = useState<string[]>(initial)
  return (
    <div style={{ width: 360 }}>
      <MultiSelect
        {...rest}
        selectedValues={selected}
        onSelectionChange={setSelected}
      />
    </div>
  )
}

export const Default: Story = {
  render: () => (
    <Interactive label='Fruits' placeholder='Pick fruits…' options={FRUITS} />
  ),
}

export const WithSelection: Story = {
  render: () => (
    <Interactive
      label='Fruits'
      options={FRUITS}
      initial={['apple', 'cherry']}
    />
  ),
}

export const WithColorMap: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Pass `colorMap` to colour-code each option and the selected chips.',
      },
    },
  },
  render: () => (
    <Interactive
      label='Fruits'
      options={FRUITS}
      initial={['apple', 'banana', 'cherry']}
      colorMap={{
        apple: colorChart1,
        banana: colorChart4,
        cherry: colorChart3,
      }}
    />
  ),
}

export const Disabled: Story = {
  render: () => (
    <Interactive label='Fruits' options={FRUITS} initial={['mango']} disabled />
  ),
}
