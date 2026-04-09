import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import WizardLayout from 'components/experiments-v2/wizard/WizardLayout'
import WizardSidebar from 'components/experiments-v2/wizard/WizardSidebar'
import WizardHeader from 'components/experiments-v2/wizard/WizardHeader'
import WizardNavButtons from 'components/experiments-v2/wizard/WizardNavButtons'
import { EXPERIMENT_WIZARD_STEPS } from 'components/experiments-v2/types'

const meta: Meta = {
  tags: ['autodocs'],
  title: 'Experiments/Wizard',
}
export default meta

type Story = StoryObj

export const FullWizard: Story = {
  decorators: [
    () => {
      const [currentStep, setCurrentStep] = useState(2)

      const stepsWithSummary = EXPERIMENT_WIZARD_STEPS.map((step, i) => {
        if (i >= currentStep) return step
        const summaries = [
          'Checkout Flow Redesign · A/B Test',
          '1 primary · 2 secondary',
        ]
        return { ...step, completeSummary: summaries[i] }
      })

      return (
        <div style={{ maxWidth: 900 }}>
          <WizardHeader
            breadcrumbs={[
              { label: 'Experiments' },
              { label: 'Create Experiment' },
            ]}
            title='Create Experiment'
            onCancel={() => alert('Cancel')}
          />

          <hr
            style={{
              border: 'none',
              borderTop: '1px solid var(--color-border-default)',
              margin: '24px 0',
            }}
          />

          <WizardLayout
            sidebar={
              <WizardSidebar
                steps={stepsWithSummary}
                currentStep={currentStep}
                onStepClick={setCurrentStep}
              />
            }
          >
            <div
              style={{
                background: 'var(--color-surface-subtle)',
                border: '1px solid var(--color-border-default)',
                borderRadius: 'var(--radius-lg)',
                color: 'var(--color-text-secondary)',
                fontSize: 14,
                padding: 32,
              }}
            >
              Step {currentStep + 1} content:{' '}
              {EXPERIMENT_WIZARD_STEPS[currentStep].title}
            </div>

            <WizardNavButtons
              isFirstStep={currentStep === 0}
              isLastStep={currentStep === EXPERIMENT_WIZARD_STEPS.length - 1}
              onBack={() => setCurrentStep(Math.max(0, currentStep - 1))}
              onContinue={() =>
                setCurrentStep(
                  Math.min(EXPERIMENT_WIZARD_STEPS.length - 1, currentStep + 1),
                )
              }
            />
          </WizardLayout>
        </div>
      )
    },
  ],
}
