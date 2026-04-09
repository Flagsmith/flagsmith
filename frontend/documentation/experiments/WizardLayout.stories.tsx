import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import WizardLayout from 'components/experiments-v2/wizard/WizardLayout'

const meta: Meta<typeof WizardLayout> = {
  component: WizardLayout,
  tags: ['autodocs'],
  title: 'Experiments/Wizard/WizardLayout',
}
export default meta

type Story = StoryObj<typeof WizardLayout>

export const Default: Story = {
  args: {
    children: (
      <div
        style={{
          background: 'var(--color-surface-subtle)',
          borderRadius: 'var(--radius-lg)',
          height: 400,
          padding: 24,
        }}
      >
        Main content area
      </div>
    ),
    sidebar: (
      <div
        style={{
          background: 'var(--color-surface-muted)',
          borderRadius: 'var(--radius-lg)',
          height: 400,
          padding: 16,
        }}
      >
        Sidebar content
      </div>
    ),
  },
}
