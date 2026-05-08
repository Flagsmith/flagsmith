import React, { FC, useCallback, useMemo, useState } from 'react'
import { useHistory, useParams } from 'react-router-dom'
import WizardLayout from './wizard/WizardLayout'
import WizardSidebar from './wizard/WizardSidebar'
import WizardHeader from './wizard/WizardHeader'
import WizardNavButtons from './wizard/WizardNavButtons'
import LivePreviewPanel from './wizard/LivePreviewPanel'
import SetupStep from './steps/SetupStep'
import SelectMetricsStep from './steps/SelectMetricsStep'
import AudienceStep from './steps/AudienceStep'
import ReviewLaunchStep from './steps/ReviewLaunchStep'
import { buildExperimentArms, splitEvenly } from './steps/AudienceStep'
import {
  EXPERIMENT_WIZARD_STEPS,
  ExperimentWizardState,
  Metric,
  MetricRole,
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

const toISODate = (d: Date) => d.toISOString().slice(0, 10)
const DEFAULT_START = new Date()
const DEFAULT_END = new Date(DEFAULT_START)
DEFAULT_END.setDate(DEFAULT_END.getDate() + 14)

const INITIAL_STATE: ExperimentWizardState = {
  audience: {
    conditions: [],
    samplePercentage: 100,
    weights: splitEvenly(INITIAL_ARMS.map((a) => a.id)),
  },
  controlValue: INITIAL_FLAG.controlValue,
  currentStep: 0,
  details: {
    endDate: toISODate(DEFAULT_END),
    hypothesis:
      'Redesigning the checkout button with a clearer CTA will increase conversion rates by at least 15% within 30 days',
    name: 'Checkout Button Redesign',
    startDate: toISODate(DEFAULT_START),
  },
  featureFlagId: INITIAL_FLAG.value,
  inclusionCriteria: 'flag-evaluated',
  inclusionEventName: '',
  layerId: null,
  metrics: [
    MOCK_METRICS[0],
    { ...MOCK_METRICS[1], role: 'secondary' },
    { ...MOCK_METRICS[2], role: 'guardrail' },
  ],
  multiVariantHandling: 'exclude',
  persistAcrossAuth: false,
  randomisationUnit: 'identity',
  sequentialTesting: false,
  statsEngine: 'bayesian',
  variations: MOCK_VARIATIONS,
}

const TOTAL_STEPS = EXPERIMENT_WIZARD_STEPS.length

const CreateExperimentPage: FC = () => {
  const history = useHistory()
  const { environmentId, projectId } = useParams<{
    projectId?: string
    environmentId?: string
  }>()
  const experimentsUrl =
    projectId && environmentId
      ? `/project/${projectId}/environment/${environmentId}/experiments`
      : '/experiments'
  const [state, setState] = useState<ExperimentWizardState>(INITIAL_STATE)

  const goToStep = useCallback((step: number) => {
    setState((prev) => ({ ...prev, currentStep: step }))
  }, [])

  const handleBack = useCallback(() => {
    goToStep(Math.max(0, state.currentStep - 1))
  }, [state.currentStep, goToStep])

  const handleLaunch = useCallback(() => {
    const flag = MOCK_FLAGS.find((f) => f.value === state.featureFlagId)
    const conditionCount = state.audience.conditions.length
    const audienceLabel =
      conditionCount === 0
        ? 'all users in the environment'
        : `users matching ${conditionCount} condition${
            conditionCount === 1 ? '' : 's'
          }`
    openConfirm({
      body: (
        <span>
          This will start serving variations of{' '}
          <strong>{flag?.label ?? 'this flag'}</strong> to{' '}
          <strong>{state.audience.samplePercentage}%</strong> of{' '}
          <strong>{audienceLabel}</strong>. You can pause or stop the experiment
          at any time.
        </span>
      ),
      onYes: () => {
        toast(`Experiment "${state.details.name}" launched`)
        history.push(experimentsUrl)
      },
      title: 'Launch experiment?',
      yesText: 'Launch',
    })
  }, [state, history, experimentsUrl])

  const handleContinue = useCallback(() => {
    if (state.currentStep < TOTAL_STEPS - 1) {
      goToStep(state.currentStep + 1)
    } else {
      handleLaunch()
    }
  }, [state.currentStep, goToStep, handleLaunch])

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
      const hasPrimary = prev.metrics.some((m) => m.role === 'primary')
      const role: MetricRole = hasPrimary ? 'secondary' : 'primary'
      return { ...prev, metrics: [...prev.metrics, { ...metric, role }] }
    })
  }, [])

  const handleSetMetricRole = useCallback(
    (metricId: string, role: MetricRole) => {
      setState((prev) => ({
        ...prev,
        metrics: prev.metrics.map((m) =>
          m.id === metricId ? { ...m, role } : m,
        ),
      }))
    },
    [],
  )

  const isCurrentStepValid = useMemo(() => {
    if (state.currentStep === 0) {
      // Setup: name + hypothesis + flag picked + flag has enough variations
      return (
        state.details.name.trim().length > 0 &&
        state.details.hypothesis.trim().length > 0 &&
        !!state.featureFlagId &&
        state.variations.length >= MIN_VARIATIONS_FOR_EXPERIMENT
      )
    }
    if (state.currentStep === 1) {
      // Audience & Traffic: weights sum to 100, sample > 0
      const sum = (state.audience.weights ?? []).reduce(
        (s, w) => s + w.weight,
        0,
      )
      return sum === 100 && state.audience.samplePercentage > 0
    }
    return true
  }, [
    state.currentStep,
    state.details.name,
    state.details.hypothesis,
    state.featureFlagId,
    state.variations.length,
    state.audience.samplePercentage,
    state.audience.weights,
  ])

  const stepsWithSummary = EXPERIMENT_WIZARD_STEPS.map((step, i) => {
    if (i >= state.currentStep) return step

    let completeSummary: string | undefined
    switch (i) {
      case 0: {
        // Setup: name + arm count
        const armCount = state.variations.length + 1
        const flag = MOCK_FLAGS.find((f) => f.value === state.featureFlagId)
        const flagLabel = flag?.label ?? 'flag'
        const parts = [
          state.details.name || null,
          `${flagLabel}`,
          `${armCount} arm${armCount === 1 ? '' : 's'}`,
        ].filter(Boolean)
        completeSummary = parts.join(' · ')
        break
      }
      case 1: {
        // Audience & Traffic
        const splitParts = (state.audience.weights ?? [])
          .filter((w) => w.weight > 0)
          .map((w) => `${w.weight}%`)
        const split = splitParts.length > 0 ? splitParts.join('/') : null
        const conditionCount = state.audience.conditions.length
        const audienceLabel =
          conditionCount === 0
            ? 'All users'
            : `${conditionCount} condition${conditionCount === 1 ? '' : 's'}`
        const summaryParts = [
          audienceLabel,
          `${state.audience.samplePercentage}%`,
          split,
        ].filter(Boolean)
        completeSummary = summaryParts.join(' · ')
        break
      }
      case 2: {
        // Measurement
        const pCount = state.metrics.filter((m) => m.role === 'primary').length
        const sCount = state.metrics.filter(
          (m) => m.role === 'secondary',
        ).length
        const gCount = state.metrics.filter(
          (m) => m.role === 'guardrail',
        ).length
        const parts = [
          `${pCount} primary`,
          `${sCount} secondary`,
          gCount > 0 ? `${gCount} guardrail` : null,
        ].filter(Boolean)
        completeSummary = parts.join(' · ')
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
          <SetupStep
            details={state.details}
            featureFlagId={state.featureFlagId}
            controlValue={state.controlValue}
            variations={state.variations}
            onDetailsChange={(details) =>
              setState((prev) => ({ ...prev, details }))
            }
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
                  audience: {
                    ...prev.audience,
                    weights: splitEvenly(arms.map((a) => a.id)),
                  },
                  variations,
                }
              })
            }
          />
        )
      case 1: {
        const flag =
          MOCK_FLAGS.find((f) => f.value === state.featureFlagId) ?? null
        return (
          <AudienceStep
            audience={state.audience}
            flag={flag}
            controlValue={state.controlValue}
            variations={state.variations}
            environmentName='Development'
            randomisationUnit={state.randomisationUnit}
            persistAcrossAuth={state.persistAcrossAuth}
            layerId={state.layerId}
            onChange={(audience) => setState((prev) => ({ ...prev, audience }))}
            onRandomisationUnitChange={(randomisationUnit) =>
              setState((prev) => ({ ...prev, randomisationUnit }))
            }
            onPersistAcrossAuthChange={(persistAcrossAuth) =>
              setState((prev) => ({ ...prev, persistAcrossAuth }))
            }
            onLayerIdChange={(layerId) =>
              setState((prev) => ({ ...prev, layerId }))
            }
          />
        )
      }
      case 2:
        return (
          <SelectMetricsStep
            selectedMetrics={state.metrics}
            onToggleMetric={handleToggleMetric}
            onSetRole={handleSetMetricRole}
            inclusionCriteria={state.inclusionCriteria}
            inclusionEventName={state.inclusionEventName}
            statsEngine={state.statsEngine}
            multiVariantHandling={state.multiVariantHandling}
            sequentialTesting={state.sequentialTesting}
            onInclusionCriteriaChange={(inclusionCriteria) =>
              setState((prev) => ({ ...prev, inclusionCriteria }))
            }
            onInclusionEventNameChange={(inclusionEventName) =>
              setState((prev) => ({ ...prev, inclusionEventName }))
            }
            onStatsEngineChange={(statsEngine) =>
              setState((prev) => ({ ...prev, statsEngine }))
            }
            onMultiVariantHandlingChange={(multiVariantHandling) =>
              setState((prev) => ({ ...prev, multiVariantHandling }))
            }
            onSequentialTestingChange={(sequentialTesting) =>
              setState((prev) => ({ ...prev, sequentialTesting }))
            }
          />
        )
      case 3:
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
        preview={<LivePreviewPanel wizardState={state} />}
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
