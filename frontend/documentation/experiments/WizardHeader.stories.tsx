import type { Meta, StoryObj } from 'storybook'
import WizardHeader from 'components/experiments-v2/wizard/WizardHeader'

const meta: Meta<typeof WizardHeader> = {
  args: {
    onCancel: () => alert('Cancel clicked'),
  },
  component: WizardHeader,
  tags: ['autodocs'],
  title: 'Experiments/Wizard/WizardHeader',
}
export default meta

type Story = StoryObj<typeof WizardHeader>

export const Default: Story = {
  args: {
    breadcrumbs: [{ label: 'Experiments' }, { label: 'Create Experiment' }],
    title: 'Create Experiment',
  },
}

export const LongTitle: Story = {
  args: {
    breadcrumbs: [
      { label: 'Experiments' },
      { label: 'Checkout Button Redesign A/B Test' },
    ],
    title: 'Checkout Button Redesign A/B Test',
  },
}
