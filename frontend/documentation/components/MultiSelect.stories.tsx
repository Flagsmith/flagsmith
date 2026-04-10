import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import { MultiSelect } from 'components/base/select/multi-select'

const SDK_OPTIONS = [
  { label: 'flagsmith-js-sdk', value: 'js' },
  { label: 'flagsmith-python-sdk', value: 'python' },
  { label: 'flagsmith-java-sdk', value: 'java' },
  { label: 'flagsmith-go-sdk', value: 'go' },
  { label: 'flagsmith-ruby-sdk', value: 'ruby' },
]

const COLOUR_MAP = new Map([
  ['js', '#0aaddf'],
  ['python', '#7a4dfc'],
  ['java', '#ef4d56'],
  ['go', '#27ab95'],
  ['ruby', '#ff9f43'],
])

const meta: Meta<typeof MultiSelect> = {
  component: MultiSelect,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 400, minHeight: 350 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Components/MultiSelect',
}
export default meta

type Story = StoryObj<typeof MultiSelect>

export const Default: Story = {
  decorators: [
    () => {
      const [selected, setSelected] = useState<string[]>([])
      return (
        <MultiSelect
          options={SDK_OPTIONS}
          selectedValues={selected}
          onSelectionChange={setSelected}
          placeholder='Select SDKs...'
        />
      )
    },
  ],
}

export const WithLabel: Story = {
  decorators: [
    () => {
      const [selected, setSelected] = useState<string[]>([])
      return (
        <MultiSelect
          label='Filter by SDK'
          options={SDK_OPTIONS}
          selectedValues={selected}
          onSelectionChange={setSelected}
        />
      )
    },
  ],
}

export const WithColors: Story = {
  decorators: [
    () => {
      const [selected, setSelected] = useState<string[]>(['js', 'python'])
      return (
        <MultiSelect
          label='Filter by SDK'
          options={SDK_OPTIONS}
          selectedValues={selected}
          onSelectionChange={setSelected}
          colorMap={COLOUR_MAP}
        />
      )
    },
  ],
}

export const PreSelected: Story = {
  decorators: [
    () => {
      const [selected, setSelected] = useState<string[]>([
        'js',
        'python',
        'java',
      ])
      return (
        <MultiSelect
          label='Selected SDKs'
          options={SDK_OPTIONS}
          selectedValues={selected}
          onSelectionChange={setSelected}
          colorMap={COLOUR_MAP}
        />
      )
    },
  ],
}

export const Disabled: Story = {
  decorators: [
    () => (
      <MultiSelect
        label='Disabled'
        options={SDK_OPTIONS}
        selectedValues={['js']}
        onSelectionChange={() => {}}
        disabled
      />
    ),
  ],
}

export const Inline: Story = {
  decorators: [
    () => {
      const [selected, setSelected] = useState<string[]>(['js', 'python'])
      return (
        <MultiSelect
          label='Inline mode'
          options={SDK_OPTIONS}
          selectedValues={selected}
          onSelectionChange={setSelected}
          inline
        />
      )
    },
  ],
}

export const Small: Story = {
  decorators: [
    () => {
      const [selected, setSelected] = useState<string[]>([])
      return (
        <MultiSelect
          label='Small size'
          options={SDK_OPTIONS}
          selectedValues={selected}
          onSelectionChange={setSelected}
          size='small'
        />
      )
    },
  ],
}
