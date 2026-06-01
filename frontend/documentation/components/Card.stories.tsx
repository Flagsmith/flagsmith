import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Card from 'components/Card'

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'Plain styled surface — rounded container with padding and a subtle border. Use it as a content block on a page; for a header + body shape with title/action slots, use `Panel`.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Patterns/Card',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <Card>
      <h5>Card title</h5>
      <p className='text-secondary mb-0'>Card content goes here.</p>
    </Card>
  ),
}

export const Nested: Story = {
  render: () => (
    <Card>
      <h5>Outer card</h5>
      <Card className='mt-3'>
        <p className='mb-0'>Nested card content.</p>
      </Card>
    </Card>
  ),
}
