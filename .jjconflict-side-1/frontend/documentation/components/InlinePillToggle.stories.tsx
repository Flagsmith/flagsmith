import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import InlinePillToggle from 'components/base/forms/InlinePillToggle'

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'A compact inline segmented control for toggling between two or more options. Available in small, medium, and large sizes.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Forms/InlinePillToggle',
}
export default meta

type Story = StoryObj

const options = [
  { label: 'ALL', value: 'ALL' },
  { label: 'ANY', value: 'ANY' },
]

function SmallExample() {
  const [value, setValue] = useState('ALL')
  return (
    <InlinePillToggle
      size='small'
      options={options}
      value={value}
      onChange={setValue}
    />
  )
}

function MediumExample() {
  const [value, setValue] = useState('ALL')
  return (
    <InlinePillToggle
      size='medium'
      options={options}
      value={value}
      onChange={setValue}
    />
  )
}

function LargeExample() {
  const [value, setValue] = useState('ALL')
  return (
    <InlinePillToggle
      size='large'
      options={options}
      value={value}
      onChange={setValue}
    />
  )
}

function InlineWithTextExample() {
  const [value, setValue] = useState('ALL')
  return (
    <span style={{ fontSize: 14, fontWeight: 600 }}>
      Include users when{' '}
      <InlinePillToggle
        size='small'
        options={options}
        value={value}
        onChange={setValue}
      />{' '}
      of the following rules apply:
    </span>
  )
}

function ThreeOptionsExample() {
  const [value, setValue] = useState('day')
  return (
    <InlinePillToggle
      options={[
        { label: 'Day', value: 'day' },
        { label: 'Week', value: 'week' },
        { label: 'Month', value: 'month' },
      ]}
      value={value}
      onChange={setValue}
    />
  )
}

export const Small: Story = { render: () => <SmallExample /> }
export const Medium: Story = { render: () => <MediumExample /> }
export const Large: Story = { render: () => <LargeExample /> }
export const InlineWithText: Story = { render: () => <InlineWithTextExample /> }
export const ThreeOptions: Story = { render: () => <ThreeOptionsExample /> }
