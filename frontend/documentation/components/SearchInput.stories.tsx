import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import SearchInput from 'components/base/forms/SearchInput'

const meta: Meta<typeof SearchInput> = {
  component: SearchInput,
  parameters: { layout: 'padded' },
  title: 'Components/Forms/SearchInput',
}
export default meta

type Story = StoryObj<typeof SearchInput>

const Interactive = () => {
  const [value, setValue] = useState('')
  return (
    <SearchInput
      placeholder='Search…'
      value={value}
      onChange={(e) => setValue(e.target.value)}
    />
  )
}

export const Default: Story = {
  render: () => <Interactive />,
}

export const Sizes: Story = {
  render: () => (
    <div className='d-flex flex-column gap-3'>
      <SearchInput placeholder='Default' />
      <SearchInput size='small' placeholder='Small' />
      <SearchInput size='xSmall' placeholder='Extra small' />
    </div>
  ),
}

export const Disabled: Story = {
  render: () => (
    <SearchInput value='read-only' disabled placeholder='Search…' />
  ),
}
