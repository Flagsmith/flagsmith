import React, { FC, FormEvent } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Checkbox from 'components/base/forms/Checkbox'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/messages/ErrorMessage'
import isFreeEmailDomain from 'common/utils/isFreeEmailDomain'
import { Req } from 'common/types/requests'

type OnboardingOrganisationFormProps = {
  onboarding: Req['register']
  error: any
  isValid: boolean
  isSaving: boolean
  setFieldValue: (key: keyof Req['register'], value: any) => void
  onSubmit: () => void
  onBack: () => void
}

const OnboardingOrganisationForm: FC<OnboardingOrganisationFormProps> = ({
  error,
  isSaving,
  isValid,
  onBack,
  onSubmit,
  onboarding,
  setFieldValue,
}) => {
  const isCompanyEmail = !isFreeEmailDomain(onboarding.email)

  return (
    <form
      onSubmit={(e: FormEvent) => {
        e.preventDefault()
        if (isValid) onSubmit()
      }}
    >
      {isSaving ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
        <>
          <div className='col-md-12'>
            <InputGroup
              title='Organisation Name'
              className='mb-0'
              inputProps={{
                autoFocus: true,
                className: 'full-width',
                name: 'organisation_name',
              }}
              value={onboarding.organisation_name}
              onChange={(e: FormEvent) => setFieldValue('organisation_name', e)}
            />
          </div>
          {isCompanyEmail && (
            <div className='col-md-12 py-3'>
              <Checkbox
                label='Opt in to a free technical onboarding call. No strings, just booleans. You won’t be subscribed to any marketing communications.'
                checked={onboarding.contact_consent_given}
                onChange={(e) => setFieldValue('contact_consent_given', e)}
              />
            </div>
          )}
          <ErrorMessage error={error} />
          <div className='d-flex mt-4 gap-2'>
            <Button className='px-4' onClick={onBack} theme='secondary'>
              Back
            </Button>
            <Button type='submit' disabled={!isValid}>
              Next
            </Button>
          </div>
        </>
      )}
    </form>
  )
}

export default OnboardingOrganisationForm
