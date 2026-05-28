import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import InputGroup from 'components/base/forms/InputGroup'
import StepShell from 'web/components/pages/onboarding-quickstart/components/StepShell'

type ProjectStepProps = {
  onBack: () => void
  onChange: (value: string) => void
  onNext: () => void
  value: string
}

const ProjectStep: FC<ProjectStepProps> = ({
  onBack,
  onChange,
  onNext,
  value,
}) => {
  const isValid = !!value.trim()

  return (
    <StepShell
      title='Name your first project'
      subtitle='The app you’re working on, or anything else.'
      body={
        <InputGroup
          title='Project name'
          inputProps={{
            className: 'w-50',
            name: 'projectName',
            onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => {
              if (e.key === 'Enter' && isValid) {
                e.preventDefault()
                onNext()
              }
            },
          }}
          value={value}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            onChange(e.target.value)
          }
          isValid={isValid}
        />
      }
      footer={
        <>
          <Button theme='text' onClick={onBack}>
            ← Back
          </Button>
          <Button theme='primary' onClick={onNext} disabled={!isValid}>
            Next →
          </Button>
        </>
      }
    />
  )
}

export default ProjectStep
