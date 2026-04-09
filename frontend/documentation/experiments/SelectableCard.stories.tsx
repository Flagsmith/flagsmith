import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import SelectableCard from 'components/experiments-v2/shared/SelectableCard'

const meta: Meta<typeof SelectableCard> = {
  component: SelectableCard,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 300 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/SelectableCard',
}
export default meta

type Story = StoryObj<typeof SelectableCard>

export const WithIcon: Story = {
  args: {
    description: 'Compare two variations',
    icon: 'bar-chart',
    onClick: () => {},
    selected: true,
    title: 'A/B Test',
  },
}

export const WithBadge: Story = {
  args: {
    badge: { label: 'Primary', variant: 'primary' },
    description: 'Percentage of users completing checkout',
    onClick: () => {},
    selected: true,
    title: 'Checkout Conversion Rate',
  },
}

export const Unselected: Story = {
  args: {
    description: 'Test multiple variables',
    icon: 'layers',
    onClick: () => {},
    selected: false,
    title: 'Multivariate',
  },
}

export const SecondaryBadge: Story = {
  args: {
    badge: { label: 'Secondary', variant: 'secondary' },
    description: 'Average revenue generated per user session',
    onClick: () => {},
    selected: true,
    title: 'Revenue per User',
  },
}

export const InteractiveGroup: Story = {
  decorators: [
    () => {
      const [selected, setSelected] = useState(0)
      const items = [
        {
          description: 'Compare two variations',
          icon: 'bar-chart' as const,
          title: 'A/B Test',
        },
        {
          description: 'Test multiple variables',
          icon: 'layers' as const,
          title: 'Multivariate',
        },
        {
          description: 'Toggle feature on/off',
          icon: 'features' as const,
          title: 'Feature Flag',
        },
      ]
      return (
        <div style={{ display: 'flex', gap: 12, maxWidth: 700 }}>
          {items.map((item, i) => (
            <SelectableCard
              key={i}
              icon={item.icon}
              title={item.title}
              description={item.description}
              selected={selected === i}
              onClick={() => setSelected(i)}
            />
          ))}
        </div>
      )
    },
  ],
}
