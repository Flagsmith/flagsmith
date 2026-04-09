import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import VariationTable from 'components/experiments-v2/shared/VariationTable'
import { MOCK_VARIATIONS } from 'components/experiments-v2/types'

const meta: Meta<typeof VariationTable> = {
  component: VariationTable,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 700 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/VariationTable',
}
export default meta

type Story = StoryObj<typeof VariationTable>

export const TwoVariations: Story = {
  args: {
    variations: MOCK_VARIATIONS,
  },
}

export const ThreeVariations: Story = {
  args: {
    variations: [
      ...MOCK_VARIATIONS,
      {
        colour: 'var(--orange-500)',
        description: 'Alternative CTA text with urgency messaging',
        id: 'var-3',
        name: 'Treatment C',
        value: 'false',
      },
    ],
  },
}

export const Editable: Story = {
  args: {
    editable: true,
    onRemove: (id: string) => alert(`Remove ${id}`),
    variations: MOCK_VARIATIONS,
  },
}
