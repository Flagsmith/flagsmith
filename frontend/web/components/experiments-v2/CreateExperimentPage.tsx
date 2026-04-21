import React, { FC, useCallback, useMemo, useState } from 'react'
import { useHistory } from 'react-router-dom'
import WizardLayout from './wizard/WizardLayout'
import WizardSidebar from './wizard/WizardSidebar'
import WizardHeader from './wizard/WizardHeader'
import WizardNavButtons from './wizard/WizardNavButtons'
import ExperimentDetailsStep from './steps/ExperimentDetailsStep'
import SelectMetricsStep from './steps/SelectMetricsStep'
import FlagVariationsStep from './steps/FlagVariationsStep'
import SegmentTrafficStep from './steps/SegmentTrafficStep'
import ReviewLaunchStep from './steps/ReviewLaunchStep'
import { buildExperimentArms, splitEvenly } from './steps/SegmentTrafficStep'
import {
  EXPERIMENT_WIZARD_STEPS,
  ExperimentWizardState,
  Metric,
  MIN_VARIATIONS_FOR_EXPERIMENT,
  MOCK_FLAGS,
  MOCK_METRICS,
  MOCK_VARIATIONS,
  Variation,
} from './types'
import './CreateExperimentPage.scss'

const INITIAL_FLAG = MOCK_FLAGS[0]
const INITIAL_ARMS = buildExperimentArms(
  INITIAL_FLAG.controlValue,
  INITIAL_FLAG.variations,
)

const INITIAL_STATE: ExperimentWizardState = {
  controlValue: INITIAL_FLAG.controlValue,
  currentStep: 0,
  details: {
    endDate: '2026-05-15',
    hypothesis:
      'Redesigning the checkout button with a clearer CTA will increase conversion rates by at least 15% within 30 days',
    name: 'Checkout Button Redesign',
    startDate: '2026-04-15',
  },
  featureFlagId: INITIAL_FLAG.value,
  metrics: [
    MOCK_METRICS[0],
    { ...MOCK_METRICS[1], role: 'secondary' },
    { ...MOCK_METRICS[2], role: 'secondary' },
  ],
  segmentTraffic: {
    segmentId: 'seg-3',
    weights: splitEvenly(INITIAL_ARMS.map((a) => a.id)),
  },
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

  const isCurrentStepValid = useMemo(() => {
    if (state.currentStep === 0) {
      return (
        state.details.name.trim().length > 0 &&
        state.details.hypothesis.trim().length > 0
      )
    }
    if (state.currentStep === 1) {
      return (
        !!state.featureFlagId &&
        state.variations.length >= MIN_VARIATIONS_FOR_EXPERIMENT
      )
    }
    if (state.currentStep === 3) {
      if (!state.segmentTraffic.segmentId) return false
      const sum = (state.segmentTraffic.weights ?? []).reduce(
        (s, w) => s + w.weight,
        0,
      )
      return sum === 100
    }
    return true
  }, [
    state.currentStep,
    state.details.name,
    state.details.hypothesis,
    state.featureFlagId,
    state.variations.length,
    state.segmentTraffic.segmentId,
    state.segmentTraffic.weights,
  ])

  const stepsWithSummary = EXPERIMENT_WIZARD_STEPS.map((step, i) => {
    if (i >= state.currentStep) return step

    let completeSummary: string | undefined
    switch (i) {
      case 0:
        completeSummary = state.details.name || undefined
        break
      case 1: {
        const armCount = state.variations.length + 1
        completeSummary = `${armCount} arm${armCount === 1 ? '' : 's'}`
        break
      }
      case 2:
        completeSummary = `${
          state.metrics.filter((m) => m.role === 'primary').length
        } primary · ${
          state.metrics.filter((m) => m.role === 'secondary').length
        } secondary`
        break
      case 3: {
        const parts = (state.segmentTraffic.weights ?? [])
          .filter((w) => w.weight > 0)
          .map((w) => `${w.weight}%`)
        completeSummary = parts.length > 0 ? parts.join(' / ') : undefined
        break
      }
      default:
        break
    }
    return { ...step, completeSummary }
  })

  const renderStepContent = () => {
    switch (state.currentStep) {
      case 0:
        return (
          <ExperimentDetailsStep
            details={state.details}
            onChange={(details) => setState((prev) => ({ ...prev, details }))}
          />
        )
      case 1:
        return (
          <FlagVariationsStep
            featureFlagId={state.featureFlagId}
            controlValue={state.controlValue}
            variations={state.variations}
            onFlagChange={(flagId) =>
              setState((prev) => ({ ...prev, featureFlagId: flagId }))
            }
            onControlValueChange={(controlValue) =>
              setState((prev) => ({ ...prev, controlValue }))
            }
            onVariationsChange={(variations: Variation[]) =>
              setState((prev) => {
                const arms = buildExperimentArms(prev.controlValue, variations)
                return {
                  ...prev,
                  segmentTraffic: {
                    ...prev.segmentTraffic,
                    weights: splitEvenly(arms.map((a) => a.id)),
                  },
                  variations,
                }
              })
            }
          />
        )
      case 2:
        return (
          <SelectMetricsStep
            selectedMetrics={state.metrics}
            onToggleMetric={handleToggleMetric}
          />
        )
      case 3: {
        const flag =
          MOCK_FLAGS.find((f) => f.value === state.featureFlagId) ?? null
        return (
          <SegmentTrafficStep
            segmentTraffic={state.segmentTraffic}
            flag={flag}
            controlValue={state.controlValue}
            variations={state.variations}
            environmentName='Development'
            onChange={(segmentTraffic) =>
              setState((prev) => ({ ...prev, segmentTraffic }))
            }
          />
        )
      }
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
          continueDisabled={!isCurrentStepValid}
        />
      </WizardLayout>
    </div>
  )
}

CreateExperimentPage.displayName = 'CreateExperimentPage'
export default CreateExperimentPage
