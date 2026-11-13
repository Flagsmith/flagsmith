import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Radio from 'components/base/forms/Radio'

const meta: Meta = {
  parameters: { layout: 'centered' },
  title: 'Components/Forms/Radio',
}
export default meta

type Story = StoryObj

type Option = 'a' | 'b'

const Group = () => {
  const [value, setValue] = useState<Option>('a')
  return (
    <div
      role='radiogroup'
      aria-label='Options'
      className='d-flex flex-column gap-1'
    >
      <Radio name='story' value='a' checked={value === 'a'} onChange={setValue}>
        Option A
      </Radio>
      <Radio name='story' value='b' checked={value === 'b'} onChange={setValue}>
        Option B
      </Radio>
    </div>
  )
}

export const Default: Story = {
  render: () => <Group />,
}

export const States: Story = {
  render: () => (
    <div className='d-flex flex-column gap-2'>
      <Radio name='states-1' value='a' checked={false} onChange={() => {}}>
        Unselected
      </Radio>
      <Radio name='states-2' value='a' checked onChange={() => {}}>
        Selected
      </Radio>
      <Radio
        name='states-3'
        value='a'
        checked={false}
        disabled
        onChange={() => {}}
      >
        Disabled
      </Radio>
    </div>
  ),
}

export const IndicatorAtEnd: Story = {
  parameters: { layout: 'padded' },
  render: () => (
    <div className='w-100'>
      <Radio
        name='end'
        value='a'
        checked
        indicatorPosition='end'
        onChange={() => {}}
      >
        <span className='flex-fill'>Full-width row</span>
      </Radio>
    </div>
  ),
}
