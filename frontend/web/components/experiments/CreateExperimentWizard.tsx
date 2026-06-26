import { FC, useCallback, useEffect, useMemo, useState } from 'react'
import { ExpectedDirection, Metric, ProjectFlag } from 'common/types/responses'
import {
  useCreateExperimentMutation,
  useStartExperimentMutation,
} from 'common/services/useExperiment'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import {
  ENABLE_EXPERIMENT_LIFECYCLE,
  METRIC_DIRECTION_TO_EXPECTED_DIRECTION,
} from './constants'
import WizardStepper from './WizardStepper'
import WizardNavButtons from './WizardNavButtons'
import LivePreviewPanel from './LivePreviewPanel'
import SetupStep from './steps/SetupStep'
import RolloutStep from './steps/RolloutStep'
import {
  VariationSplitEntry,
  getControlPercentage,
  getVariationSplitDefaults,
  toRolloutFeatureValue,
} from './rollout'
import MeasurementStep from './steps/MeasurementStep'
import ReviewStep from './steps/ReviewStep'

const TOTAL_STEPS = 4
const MEASUREMENT_STEP = 2
const SHOW_LIVE_PREVIEW = false

type CreateExperimentWizardProps = {
  environmentId: string
  projectId: number
  onCreated: () => void
}

const CreateExperimentWizard: FC<CreateExperimentWizardProps> = ({
  environmentId,
  onCreated,
  projectId,
}) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [name, setName] = useState('')
  const [hypothesis, setHypothesis] = useState('')
  const [selectedFeature, setSelectedFeature] = useState<ProjectFlag | null>(
    null,
  )
  const [selectedMetric, setSelectedMetric] = useState<Metric | null>(null)
  const [expectedDirection, setExpectedDirection] =
    useState<ExpectedDirection | null>(null)
  const [rolloutPercentage, setRolloutPercentage] = useState(100)
  const [variationSplit, setVariationSplit] = useState<VariationSplitEntry[]>(
    [],
  )
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set())

  const { getEnvironmentIdFromKey } = useProjectEnvironments(projectId)
  const numericEnvId = getEnvironmentIdFromKey(environmentId)

  const { data: featureStatesData } = useGetFeatureStatesQuery(
    { environment: numericEnvId, feature: selectedFeature?.id },
    { skip: !selectedFeature || !numericEnvId },
  )

  const environmentFeatureState = useMemo(
    () =>
      featureStatesData?.results?.find(
        (state) => !state.feature_segment && !state.identity,
      ),
    [featureStatesData],
  )

  useEffect(() => {
    setVariationSplit(
      selectedFeature
        ? getVariationSplitDefaults(
            selectedFeature.multivariate_options,
            environmentFeatureState?.multivariate_feature_state_values,
          )
        : [],
    )
  }, [selectedFeature, environmentFeatureState])

  const [createExperiment, { isLoading: isCreating }] =
    useCreateExperimentMutation()
  const [startExperiment, { isLoading: isStarting }] =
    useStartExperimentMutation()
  const isSubmitting = isCreating || isStarting

  const isStep1Valid = useMemo(
    () =>
      name.trim().length > 0 &&
      hypothesis.trim().length > 0 &&
      selectedFeature !== null,
    [name, hypothesis, selectedFeature],
  )

  const isMeasurementValid =
    selectedMetric !== null && expectedDirection !== null

  const controlPercentage = getControlPercentage(variationSplit)
  const isRolloutValid =
    rolloutPercentage > 0 && controlPercentage >= 0 && controlPercentage <= 100

  const stepValidity: Record<number, boolean> = {
    0: isStep1Valid,
    1: isRolloutValid,
    3: isStep1Valid && isRolloutValid && isMeasurementValid,
    [MEASUREMENT_STEP]: isMeasurementValid,
  }
  const canContinue = stepValidity[currentStep] ?? true

  const handleMetricSelect = useCallback((metric: Metric) => {
    setSelectedMetric(metric)
    setExpectedDirection(
      METRIC_DIRECTION_TO_EXPECTED_DIRECTION[metric.direction],
    )
  }, [])

  const handleContinue = useCallback(() => {
    if (currentStep < TOTAL_STEPS - 1) {
      setCompletedSteps((prev) => new Set(prev).add(currentStep))
      setCurrentStep(currentStep + 1)
    }
  }, [currentStep])

  const handleBack = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }, [currentStep])

  const handleStepClick = useCallback(
    (step: number) => {
      if (completedSteps.has(step) || step < currentStep) {
        setCurrentStep(step)
      }
    },
    [completedSteps, currentStep],
  )

  const doCreate = useCallback(async () => {
    if (!selectedFeature || !selectedMetric || !expectedDirection) return
    try {
      const controlValue =
        selectedFeature.environment_feature_state?.feature_state_value ?? ''
      const experiment = await createExperiment({
        body: {
          experiment_rollout: {
            enabled: false,
            feature_state_value: toRolloutFeatureValue(controlValue),
            multivariate_feature_state_values: variationSplit,
            rollout_percentage: rolloutPercentage,
          },
          feature: selectedFeature.id,
          hypothesis: hypothesis.trim(),
          metrics: [
            {
              expected_direction: expectedDirection,
              metric: selectedMetric.id,
            },
          ],
          name: name.trim(),
        },
        environmentId,
      }).unwrap()
      // Auto-start to skip draft status when lifecycle states are disabled.
      if (!ENABLE_EXPERIMENT_LIFECYCLE) {
        try {
          await startExperiment({
            environmentId,
            experimentId: experiment.id,
          }).unwrap()
        } catch {
          toast(
            'Experiment created but failed to start. You can start it manually from the experiment page.',
            'danger',
          )
          onCreated()
          return
        }
      }
      toast('Experiment created and started')
      onCreated()
    } catch {
      toast('Failed to create experiment', 'danger')
    }
  }, [
    createExperiment,
    environmentId,
    expectedDirection,
    hypothesis,
    name,
    onCreated,
    rolloutPercentage,
    selectedFeature,
    selectedMetric,
    startExperiment,
    variationSplit,
  ])

  const handleLaunch = useCallback(() => {
    if (!selectedFeature || !isMeasurementValid) return
    openConfirm({
      body: (
        <span>
          This will start serving variations of{' '}
          <strong>{selectedFeature.name}</strong> to{' '}
          <strong>
            {rolloutPercentage}% of eligible identities in the environment
          </strong>
          . While the experiment is running, the flag value will not be
          editable.
        </span>
      ),
      noText: 'Cancel',
      onYes: doCreate,
      title: 'Create experiment?',
      yesText: 'Create',
    })
  }, [selectedFeature, isMeasurementValid, rolloutPercentage, doCreate])

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <SetupStep
            name={name}
            hypothesis={hypothesis}
            selectedFeature={selectedFeature}
            projectId={projectId}
            environmentId={environmentId}
            onNameChange={setName}
            onHypothesisChange={setHypothesis}
            onFeatureSelect={setSelectedFeature}
          />
        )
      case 1:
        return (
          <RolloutStep
            selectedFeature={selectedFeature}
            rolloutPercentage={rolloutPercentage}
            variationSplit={variationSplit}
            onRolloutChange={setRolloutPercentage}
            onSplitChange={setVariationSplit}
          />
        )
      case 2:
        return (
          <MeasurementStep
            environmentId={environmentId}
            selectedMetric={selectedMetric}
            expectedDirection={expectedDirection}
            onMetricSelect={handleMetricSelect}
            onExpectedDirectionChange={setExpectedDirection}
          />
        )
      case 3:
        return (
          <ReviewStep
            name={name}
            hypothesis={hypothesis}
            selectedFeature={selectedFeature}
            selectedMetric={selectedMetric}
            expectedDirection={expectedDirection}
            rolloutPercentage={rolloutPercentage}
            variationSplit={variationSplit}
            onEditSetup={() => setCurrentStep(0)}
            onEditMeasurement={() => setCurrentStep(MEASUREMENT_STEP)}
            onEditRollout={() => setCurrentStep(1)}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className='d-flex gap-4'>
      <WizardStepper
        currentStep={currentStep}
        completedSteps={completedSteps}
        onStepClick={handleStepClick}
      />
      <div className='flex-fill' style={{ minWidth: 0 }}>
        {renderStep()}
        <WizardNavButtons
          currentStep={currentStep}
          totalSteps={TOTAL_STEPS}
          canContinue={canContinue}
          isSubmitting={isSubmitting}
          onBack={handleBack}
          onContinue={handleContinue}
          onLaunch={handleLaunch}
        />
      </div>
      {SHOW_LIVE_PREVIEW && <LivePreviewPanel />}
    </div>
  )
}

export default CreateExperimentWizard
