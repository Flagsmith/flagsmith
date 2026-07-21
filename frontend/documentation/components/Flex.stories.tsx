import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Flex from 'components/base/grid/Flex'

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Components/Layout/Flex',
}
export default meta

type Story = StoryObj

const Block: React.FC<{ label: string }> = ({ label }) => (
  <div className='bg-surface-subtle rounded-1 p-3'>{label}</div>
)

export const Default: Story = {
  render: () => (
    <div className='d-flex gap-2' style={{ width: 480 }}>
      <Flex>
        <Block label='Flex grows to fill' />
      </Flex>
      <Block label='Fixed' />
    </div>
  ),
}

export const TwoFlex: Story = {
  render: () => (
    <div className='d-flex gap-2' style={{ width: 480 }}>
      <Flex>
        <Block label='Flex 1' />
      </Flex>
      <Flex>
        <Block label='Flex 1' />
      </Flex>
    </div>
  ),
}
