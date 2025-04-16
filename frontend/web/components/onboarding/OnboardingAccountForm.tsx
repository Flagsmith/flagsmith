// OnboardingAccountForm.tsx
import React, { FC, FormEvent } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import InfoMessage from 'components/InfoMessage'
import PasswordRequirements from 'components/PasswordRequirements'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import isFreeEmailDomain from 'common/utils/isFreeEmailDomain'
import { Req } from 'common/types/requests'

type OnboardingAccountFormProps = {
  onboarding: Req['createOnboarding']
  error: any
  isValid: boolean
  setFieldValue: (key: keyof Req['createOnboarding'], value: any) => void
  onSubmit: () => void
  onRequirementsMet: (met: boolean) => void
}

const OnboardingAccountForm: FC<OnboardingAccountFormProps> = ({
  error,
  isValid,
  onRequirementsMet,
  onSubmit,
  onboarding,
  setFieldValue,
}) => {
  const isValidEmail = Utils.isValidEmail(onboarding.email)

  return (
    <form
      onSubmit={(e: FormEvent) => {
        e.preventDefault()
        if (isValid) onSubmit()
      }}
    >
      <div className='row row-gap-4'>
        <div className='col-md-6'>
          <InputGroup
            title='First Name'
            className='mb-0'
            isValid={!!onboarding.first_name && !error?.first_name}
            inputProps={{
              autoFocus: true,
              className: 'full-width',
              error: error?.first_name,
              name: 'first_name',
            }}
            value={onboarding.first_name}
            onChange={(e: FormEvent) => setFieldValue('first_name', e)}
          />
        </div>
        <div className='col-md-6'>
          <InputGroup
            title='Last Name'
            className='mb-0'
            isValid={!!onboarding.last_name && !error?.last_name}
            inputProps={{
              className: 'full-width',
              error: error?.last_name,
              name: 'last_name',
            }}
            value={onboarding.last_name}
            onChange={(e: FormEvent) => setFieldValue('last_name', e)}
          />
        </div>
        <div className='col-md-12'>
          <InputGroup
            title='Email'
            type='email'
            className='mb-0'
            isValid={isValidEmail && !error?.email}
            inputProps={{
              className: 'full-width',
              error: error?.email,
              name: 'email',
            }}
            value={onboarding.email}
            onChange={(e: FormEvent) => setFieldValue('email', e)}
          />
        </div>
        {isFreeEmailDomain(onboarding.email) && (
          <div>
            <InfoMessage>
              Signing up with a work email makes it easier for co-workers to
              join your Flagsmith organisation.
            </InfoMessage>
          </div>
        )}
        <div className='col-md-12'>
          <InputGroup
            title='Password'
            data-test='password'
            isValid={isValid}
            inputProps={{
              className: 'full-width',
              isValid: isValid,
              name: 'password',
            }}
            onChange={(e: FormEvent) => setFieldValue('password', e)}
            className='mb-0 full-width'
            type='password'
            name='password'
            id='password'
          />
          <PasswordRequirements
            password={onboarding.password}
            onRequirementsMet={onRequirementsMet}
          />
        </div>
        <div className='col-md-12'>
          <Button type='submit' disabled={!isValid}>
            Next
          </Button>
        </div>
      </div>
    </form>
  )
}

export default OnboardingAccountForm
