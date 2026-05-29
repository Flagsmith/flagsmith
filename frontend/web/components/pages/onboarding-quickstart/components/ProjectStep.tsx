import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import InputGroup from 'components/base/forms/InputGroup'
import StepShell from 'web/components/pages/onboarding-quickstart/components/StepShell'

type ProjectStepProps = {
  onBack: () => void
  onChange: (value: string) => void
  onNext: () => void
  placeholder: string
  value: string
}

const ProjectStep: FC<ProjectStepProps> = ({
  onBack,
  onChange,
  onNext,
  placeholder,
  value,
}) => {
  const hasValue = !!value.trim()
  // The placeholder ('My first project') is a real fallback — leaving the
  // field blank uses it, so the user can advance without typing anything.
  const canProceed = hasValue || !!placeholder

  return (
    <StepShell
      title='Name your first project'
      subtitle='The app you’re working on, or anything else.'
      body={
        <InputGroup
          title='Project name'
          placeholder={placeholder}
          inputProps={{
            className: 'w-50',
            name: 'projectName',
            onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => {
              if (e.key === 'Enter' && canProceed) {
                e.preventDefault()
                onNext()
              }
            },
          }}
          value={value}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            onChange(e.target.value)
          }
          isValid={hasValue}
        />
      }
      footer={
        <>
          <Button theme='text' onClick={onBack}>
            ← Back
          </Button>
          <Button theme='primary' onClick={onNext} disabled={!canProceed}>
            Next →
          </Button>
        </>
      }
    />
  )
}

export default ProjectStep
