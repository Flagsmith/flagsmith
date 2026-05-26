import { FC, useCallback, useMemo, useState } from 'react'
import { ProjectFlag } from 'common/types/responses'
import { useCreateExperimentMutation } from 'common/services/useExperiment'
import WizardStepper from './WizardStepper'
import WizardNavButtons from './WizardNavButtons'
import LivePreviewPanel from './LivePreviewPanel'
import SetupStep from './steps/SetupStep'
import AudienceStep from './steps/AudienceStep'
import MeasurementStep from './steps/MeasurementStep'
import ReviewStep from './steps/ReviewStep'

const TOTAL_STEPS = 4

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
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set())

  const [createExperiment, { isLoading: isSubmitting }] =
    useCreateExperimentMutation()

  const isStep1Valid = useMemo(
    () =>
      name.trim().length > 0 &&
      hypothesis.trim().length > 0 &&
      selectedFeature !== null,
    [name, hypothesis, selectedFeature],
  )

  const canContinue = currentStep === 0 ? isStep1Valid : true

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
    if (!selectedFeature) return
    try {
      await createExperiment({
        body: {
          feature: selectedFeature.id,
          hypothesis: hypothesis.trim(),
          name: name.trim(),
        },
        environmentId,
      }).unwrap()
      toast('Experiment created successfully')
      onCreated()
    } catch {
      toast('Failed to create experiment', 'danger')
    }
  }, [
    createExperiment,
    environmentId,
    hypothesis,
    name,
    onCreated,
    selectedFeature,
  ])

  const handleLaunch = useCallback(() => {
    if (!selectedFeature) return
    openConfirm({
      body: (
        <span>
          This will start serving variations of{' '}
          <strong>{selectedFeature.name}</strong> to{' '}
          <strong>100% of all users in the environment</strong>. You can pause
          or stop the experiment at any time.
        </span>
      ),
      noText: 'Cancel',
      onYes: doCreate,
      title: 'Create experiment?',
      yesText: 'Create',
    })
  }, [selectedFeature, doCreate])

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
        return <AudienceStep />
      case 2:
        return <MeasurementStep />
      case 3:
        return (
          <ReviewStep
            name={name}
            hypothesis={hypothesis}
            selectedFeature={selectedFeature}
            onEditSetup={() => setCurrentStep(0)}
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
      <LivePreviewPanel />
    </div>
  )
}

export default CreateExperimentWizard
