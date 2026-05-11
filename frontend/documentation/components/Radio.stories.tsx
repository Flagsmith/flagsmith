import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Radio from 'components/base/forms/Radio'

const meta: Meta = {
  parameters: { layout: 'centered' },
  title: 'Components/Forms/Radio',
}
export default meta

type Story = StoryObj

const InteractiveRadio = () => {
  const [checked, setChecked] = useState(false)
  return <Radio label='Option A' checked={checked} onChange={setChecked} />
}

export const Default: Story = {
  render: () => <InteractiveRadio />,
}

export const States: Story = {
  render: () => (
    <div className='d-flex flex-column gap-2'>
      <Radio label='Unselected' checked={false} onChange={() => {}} />
      <Radio label='Selected' checked={true} onChange={() => {}} />
    </div>
  ),
}
