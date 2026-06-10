import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Input from 'components/base/forms/Input'

const meta: Meta = {
  parameters: { layout: 'centered' },
  title: 'Components/Forms/Input',
}
export default meta

type Story = StoryObj

const Interactive = (props: Record<string, any>) => {
  const [value, setValue] = useState(props.initialValue ?? '')
  return (
    <Input
      {...props}
      value={value}
      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
        setValue(e.target.value)
      }
    />
  )
}

export const Default: Story = {
  render: () => <Interactive placeholder='Type here...' />,
}

export const Sizes: Story = {
  render: () => (
    <div className='d-flex flex-column gap-3'>
      <Interactive size='large' placeholder='Large' />
      <Interactive placeholder='Default' />
      <Interactive size='small' placeholder='Small' />
      <Interactive size='xSmall' placeholder='xSmall' />
    </div>
  ),
}

export const Search: Story = {
  render: () => <Interactive search placeholder='Search...' />,
}

export const Password: Story = {
  render: () => (
    <Interactive type='password' initialValue='secret' placeholder='Password' />
  ),
}

// Borderless input with a bottom underline only — used for inline edits
// such as the variant label in the feature modal.
export const Underline: Story = {
  render: () => (
    <Interactive
      underline
      size='small'
      initialValue='my_variant'
      placeholder='Variant_1'
      style={{ width: 150 }}
    />
  ),
}

// Underline combined with centered, as used for the variant weight input.
export const UnderlineCentered: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-2'>
      <div style={{ width: 64 }}>
        <Interactive underline centered size='small' initialValue='50' />
      </div>
      <span className='text-muted'>%</span>
    </div>
  ),
}
