import type { Meta, StoryObj } from 'storybook'
import WizardNavButtons from 'components/experiments-v2/wizard/WizardNavButtons'

const meta: Meta<typeof WizardNavButtons> = {
  args: {
    onBack: () => alert('Back clicked'),
    onContinue: () => alert('Continue clicked'),
  },
  component: WizardNavButtons,
  tags: ['autodocs'],
  title: 'Experiments/Wizard/WizardNavButtons',
}
export default meta

type Story = StoryObj<typeof WizardNavButtons>

export const FirstStep: Story = {
  args: {
    isFirstStep: true,
  },
}

export const MiddleStep: Story = {
  args: {
    isFirstStep: false,
    isLastStep: false,
  },
}

export const LastStep: Story = {
  args: {
    isLastStep: true,
  },
}

export const Disabled: Story = {
  args: {
    continueDisabled: true,
  },
}
