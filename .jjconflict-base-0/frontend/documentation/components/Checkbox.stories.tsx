import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Checkbox from 'components/base/forms/Checkbox'

const meta: Meta = {
  parameters: { layout: 'centered' },
  title: 'Components/Forms/Checkbox',
}
export default meta

type Story = StoryObj

const InteractiveCheckbox = () => {
  const [checked, setChecked] = useState(false)
  return (
    <Checkbox label='Accept terms' checked={checked} onChange={setChecked} />
  )
}

export const Default: Story = {
  render: () => <InteractiveCheckbox />,
}

export const States: Story = {
  render: () => (
    <div className='d-flex flex-column gap-2'>
      <Checkbox label='Unchecked' checked={false} onChange={() => {}} />
      <Checkbox label='Checked' checked={true} onChange={() => {}} />
    </div>
  ),
}
