import React, { FC, useCallback, useState } from 'react'
import { useHistory } from 'react-router-dom'
import WizardLayout from './wizard/WizardLayout'
import WizardSidebar from './wizard/WizardSidebar'
import WizardHeader from './wizard/WizardHeader'
import WizardNavButtons from './wizard/WizardNavButtons'
import ExperimentDetailsStep from './steps/ExperimentDetailsStep'
import SelectMetricsStep from './steps/SelectMetricsStep'
import FlagVariationsStep from './steps/FlagVariationsStep'
import AudienceTrafficStep from './steps/AudienceTrafficStep'
import ReviewLaunchStep from './steps/ReviewLaunchStep'
import {
  EXPERIMENT_WIZARD_STEPS,
  ExperimentWizardState,
  Metric,
  MOCK_METRICS,
  MOCK_VARIATIONS,
} from './types'
import './CreateExperimentPage.scss'

const INITIAL_STATE: ExperimentWizardState = {
  audience: { segmentId: 'seg-1', splits: [], trafficPercentage: 50 },
  currentStep: 0,
  details: {
    endDate: '2026-05-15',
    hypothesis:
      'Redesigning the checkout button with a clearer CTA will increase conversion rates by at least 15% within 30 days',
    name: 'Checkout Button Redesign',
    startDate: '2026-04-15',
  },
  featureFlagId: 'flag-1',
  metrics: [
    MOCK_METRICS[0],
    { ...MOCK_METRICS[1], role: 'secondary' },
    { ...MOCK_METRICS[2], role: 'secondary' },
  ],
  variations: MOCK_VARIATIONS,
}

const TOTAL_STEPS = EXPERIMENT_WIZARD_STEPS.length

const CreateExperimentPage: FC = () => {
  const history = useHistory()
  const [state, setState] = useState<ExperimentWizardState>(INITIAL_STATE)

  const goToStep = useCallback((step: number) => {
    setState((prev) => ({ ...prev, currentStep: step }))
  }, [])

  const handleBack = useCallback(() => {
    goToStep(Math.max(0, state.currentStep - 1))
  }, [state.currentStep, goToStep])

  const handleContinue = useCallback(() => {
    if (state.currentStep < TOTAL_STEPS - 1) {
      goToStep(state.currentStep + 1)
    } else {
      // Launch — for now just alert with mock data
      alert('Experiment launched! (mock)')
    }
  }, [state.currentStep, goToStep])

  const handleCancel = useCallback(() => {
    history.goBack()
  }, [history])

  const handleToggleMetric = useCallback((metric: Metric) => {
    setState((prev) => {
      const exists = prev.metrics.find((m) => m.id === metric.id)
      if (exists) {
        return {
          ...prev,
          metrics: prev.metrics.filter((m) => m.id !== metric.id),
        }
      }
      const role = prev.metrics.length === 0 ? 'primary' : 'secondary'
      return { ...prev, metrics: [...prev.metrics, { ...metric, role }] }
    })
  }, [])

  const stepsWithSummary = EXPERIMENT_WIZARD_STEPS.map((step, i) => {
    if (i >= state.currentStep) return step

    let completeSummary: string | undefined
    switch (i) {
      case 0:
        completeSummary = `${state.variations.length} variations`
        break
      case 1:
        completeSummary = state.details.name || undefined
        break
      case 2:
        completeSummary = `${
          state.metrics.filter((m) => m.role === 'primary').length
        } primary · ${
          state.metrics.filter((m) => m.role === 'secondary').length
        } secondary`
        break
      case 3:
        completeSummary = `${state.audience.trafficPercentage}% traffic`
        break
      default:
        break
    }
    return { ...step, completeSummary }
  })

  const renderStepContent = () => {
    switch (state.currentStep) {
      case 0:
        return (
          <FlagVariationsStep
            featureFlagId={state.featureFlagId}
            variations={state.variations}
            onFlagChange={(flagId) =>
              setState((prev) => ({ ...prev, featureFlagId: flagId }))
            }
            onVariationsChange={(variations) =>
              setState((prev) => ({ ...prev, variations }))
            }
          />
        )
      case 1:
        return (
          <ExperimentDetailsStep
            details={state.details}
            onChange={(details) => setState((prev) => ({ ...prev, details }))}
          />
        )
      case 2:
        return (
          <SelectMetricsStep
            selectedMetrics={state.metrics}
            onToggleMetric={handleToggleMetric}
          />
        )
      case 3:
        return (
          <AudienceTrafficStep
            audience={state.audience}
            onChange={(audience) => setState((prev) => ({ ...prev, audience }))}
          />
        )
      case 4:
        return <ReviewLaunchStep wizardState={state} onEditStep={goToStep} />
      default:
        return null
    }
  }

  return (
    <div className='create-experiment-page'>
      <WizardHeader
        breadcrumbs={[{ label: 'Experiments' }, { label: 'Create Experiment' }]}
        title='Create Experiment'
        onCancel={handleCancel}
      />

      <div className='create-experiment-page__divider' />

      <WizardLayout
        sidebar={
          <WizardSidebar
            steps={stepsWithSummary}
            currentStep={state.currentStep}
            onStepClick={goToStep}
          />
        }
      >
        {renderStepContent()}

        <WizardNavButtons
          isFirstStep={state.currentStep === 0}
          isLastStep={state.currentStep === TOTAL_STEPS - 1}
          onBack={handleBack}
          onContinue={handleContinue}
        />
      </WizardLayout>
    </div>
  )
}

CreateExperimentPage.displayName = 'CreateExperimentPage'
export default CreateExperimentPage
