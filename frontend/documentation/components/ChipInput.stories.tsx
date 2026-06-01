import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import ChipInput from 'components/ChipInput'

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Components/Forms/ChipInput',
}
export default meta

type Story = StoryObj

const Template = ({ initial = [] }: { initial?: string[] }) => {
  const [chips, setChips] = useState<string[]>(initial)
  return (
    <div style={{ width: 360 }}>
      <ChipInput
        value={chips}
        onChange={setChips}
        placeholder='Type and press Enter or comma'
      />
    </div>
  )
}

export const Empty: Story = {
  render: () => <Template />,
}

export const WithChips: Story = {
  render: () => (
    <Template initial={['feature-flags', 'release', 'experiment']} />
  ),
}

export const SingleChip: Story = {
  render: () => <Template initial={['identity@example.com']} />,
}
