import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import InputGroup from 'components/base/forms/InputGroup'
import StepShell from 'web/components/pages/onboarding-quickstart/components/StepShell'

type OrgStepProps = {
  onChange: (value: string) => void
  onNext: () => void
  value: string
}

const OrgStep: FC<OrgStepProps> = ({ onChange, onNext, value }) => {
  const isValid = !!value.trim()

  return (
    <StepShell
      title="What's your organisation called?"
      subtitle='Pre-filled from your email domain — edit if you’d rather.'
      body={
        <InputGroup
          title='Organisation name'
          inputProps={{
            className: 'w-50',
            name: 'orgName',
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
          <span />
          <Button theme='primary' onClick={onNext} disabled={!isValid}>
            Next →
          </Button>
        </>
      }
    />
  )
}

export default OrgStep
