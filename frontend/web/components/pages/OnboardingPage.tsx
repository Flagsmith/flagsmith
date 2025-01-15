import React, { FC, useEffect, useState } from 'react'
import Logo from 'components/Logo'
import getBuildVersion from 'project/getBuildVersion'
import { Version } from 'components/BuildVersion'
import Button from 'components/base/forms/Button'
import AccountStore from 'common/stores/account-store'
import Card from 'components/Card'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import Icon from 'components/Icon'
import AppActions from 'common/dispatcher/app-actions'
import API from 'project/api'
import { RouterChildContext } from 'react-router'
import Checkbox from 'components/base/forms/Checkbox'
import { useCreateOnboardingMutation } from 'common/services/useOnboarding'
import PasswordRequirements from 'components/PasswordRequirements'

// Types
interface OnboardingPageProps {
  router: RouterChildContext['router']
}

interface StepProps {
  value: number
  setValue: (v: number) => void
  step: number
  children: React.ReactNode
  completedTitle: React.ReactNode
  title: React.ReactNode
  description: React.ReactNode
  onSubmit?: () => void
  isValid: boolean
}

const Step: FC<StepProps> = ({
  children,
  completedTitle,
  description,
  isValid,
  onSubmit,
  setValue,
  step,
  title,
  value,
}) => {
  const isComplete = value > step
  const isActive = value === step
  const numberStyle = {
    alignItems: 'center',
    borderRadius: '50%',
    display: 'flex',
    height: 33,
    justifyContent: 'center',
    left: -17.5,
    position: 'absolute',
    width: 33,
  }
  const numberClassName =
    'd-flex border-1 justify-content-center align-items-center'

  return (
    <Card
      contentClassName={isActive || isComplete ? 'bg-white' : 'bg-light200'}
      className={`rounded col-8 offset-2 position-relative border-1 px-2 ${
        isActive || isComplete ? 'bg-white' : 'bg-light200'
      }`}
    >
      <div
        className={`${numberClassName} ${
          isComplete
            ? ''
            : isActive
            ? 'bg-white bg-body text-primary fw-semibold'
            : 'bg-white bg-light200'
        }`}
        style={{
          ...numberStyle,
          ...(isComplete
            ? { backgroundColor: 'transparent', border: 'none' }
            : {}),
        }}
      >
        {isComplete ? (
          <Icon width={33} fill='#27ab95' name='checkmark-circle' />
        ) : (
          step
        )}
      </div>
      <div className='d-flex align-items-center gap-1'>
        <h5 className={`mb-0 ${isComplete ? 'text-success' : 'text-primary'}`}>
          {isComplete ? completedTitle : title}
        </h5>
      </div>

      {isActive && description && <p className='text-muted'>{description}</p>}
      {isActive && (
        <>
          <hr />
          <form
            onSubmit={(e) => {
              e.preventDefault()
              if (onSubmit && isValid) onSubmit()
            }}
          >
            <div className='row row-gap-4'>{children}</div>
          </form>
        </>
      )}
    </Card>
  )
}

const OnboardingPage: FC<OnboardingPageProps> = ({ router }) => {
  const [version, setVersion] = useState<Version>()
  const [step, setStep] = useState(0)
  const [requirementsMet, setRequirementsMet] = useState(false)

  const [onboarding, setOnboarding] = useState({
    confirm_password: '',
    email: '',
    first_name: '',
    last_name: '',
    organisation_name: '',
    password: '',
    share_details: true,
  })

  useEffect(() => {
    document.body.classList.add('onboarding')
    getBuildVersion().then(setVersion)
    return () => document.body.classList.remove('onboarding')
  }, [])

  const [createOnboarding, { error, isLoading }] = useCreateOnboardingMutation()

  const setFieldValue = (key: keyof typeof onboarding, value: any) => {
    setOnboarding({ ...onboarding, [key]: Utils.safeParseEventValue(value) })
  }

  const isStep1Valid =
    onboarding.first_name &&
    onboarding.last_name &&
    Utils.isValidEmail(onboarding.email)
  const isStep2Valid = !!onboarding.organisation_name

  const onSubmitStep1 = () => setStep(2)
  const onSubmitStep2 = async () => {
    try {
      await createOnboarding(onboarding)
      setStep(3)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className='position-fixed overflow-auto top-0 bottom-0 left-0 w-100'>
      <div className='min-vh-100 w-100 d-flex flex-1 flex-column justify-content-center align-items-center'>
        <div className='container'>
          {step ? (
            <div className='px-2 d-flex flex-column gap-3'>
              <div className='text-center'>
                <Logo size={100} />
              </div>
              <Step
                step={1}
                value={step}
                setValue={setStep}
                title='Your account'
                description='This account will be set as the Django Admin. You will be able to set up SSO and OAuth for your team members.'
                completedTitle={`Hey ${onboarding.first_name}`}
                onSubmit={onSubmitStep1}
                isValid={isStep1Valid}
              >
                <div className='col-md-6'>
                  <InputGroup
                    title='First Name'
                    className='mb-0'
                    inputProps={{
                      autoFocus: true,
                      className: 'full-width',
                      error: error && error.first_name,
                      name: 'first_name',
                    }}
                    value={onboarding.first_name}
                    onChange={(e) => setFieldValue('first_name', e)}
                  />
                </div>
                <div className='col-md-6'>
                  <InputGroup
                    title='Last Name'
                    className='mb-0'
                    inputProps={{
                      className: 'full-width',
                      error: error && error.last_name,
                      name: 'last_name',
                    }}
                    value={onboarding.last_name}
                    onChange={(e) => setFieldValue('last_name', e)}
                  />
                </div>
                <div className='col-md-12'>
                  <InputGroup
                    title='Email'
                    type='email'
                    className='mb-0'
                    inputProps={{
                      className: 'full-width',
                      error: error && error.email,
                      name: 'email',
                    }}
                    value={onboarding.email}
                    onChange={(e) => setFieldValue('email', e)}
                  />
                </div>
                <div className='col-md-12'>
                  <InputGroup
                    title='Password'
                    data-test='password'
                    inputProps={{
                      className: 'full-width',
                      error: error && error.password,
                      name: 'password',
                    }}
                    onChange={(e) => {
                      setFieldValue('password', e)
                    }}
                    className='input-default full-width'
                    type='password'
                    name='password'
                    id='password'
                  />
                  <PasswordRequirements
                    password={onboarding.password}
                    onRequirementsMet={setRequirementsMet}
                  />
                </div>
                <div className='col-md-12'>
                  <Checkbox
                    label='I consent to Flagsmith contacting me for free onboarding support.'
                    checked={onboarding.share_details}
                    onChange={(e) => setFieldValue('share_details', e)}
                  />
                </div>
                <div className='col-md-12'>
                  <Button type='submit' disabled={!isStep1Valid}>
                    Next
                  </Button>
                </div>
              </Step>
              <Step
                step={2}
                value={step}
                setValue={setStep}
                title='Your organisation'
                description='Organisations are a way for you and other team members to manage projects and their features. Users can be members of multiple organisations.'
                completedTitle={`Creating the organisation ${onboarding.organisation_name}`}
                onSubmit={onSubmitStep2}
                isValid={isStep2Valid}
              >
                <div className='col-md-12'>
                  <InputGroup
                    title='Organisation Name'
                    className='mb-0'
                    inputProps={{
                      autoFocus: true,
                      className: 'full-width',
                      error: error && error.organisation_name,
                      name: 'organisation_name',
                    }}
                    value={onboarding.organisation_name}
                    onChange={(e) => setFieldValue('organisation_name', e)}
                  />
                </div>
                <div className='d-flex gap-2'>
                  <Button
                    className='px-4'
                    onClick={() => setStep(1)}
                    theme='secondary'
                  >
                    Back
                  </Button>
                  <Button type='submit' disabled={!isStep2Valid}>
                    Next
                  </Button>
                </div>
              </Step>
              <Step
                step={3}
                value={step}
                title='Usage data preferences'
                isValid={true}
              >
                <div className='d-flex gap-2'>
                  <Button
                    className='px-4'
                    onClick={() => setStep(2)}
                    theme='secondary'
                  >
                    Back
                  </Button>
                  <Button type='submit' disabled={isLoading}>
                    Complete
                  </Button>
                </div>
                <div className='col-md-6'></div>
              </Step>
            </div>
          ) : (
            <div className='text-center'>
              <Logo size={100} />
              <h3 className='fw-semibold mt-2'>
                Welcome to Flagsmith {AccountStore.getUser()?.first_name}
              </h3>
              <h5 className='fw-normal text-muted'>
                You've successfully installed Flagsmith v{version?.tag}, let's
                get started!
              </h5>
              <Button onClick={() => setStep(1)} className='mt-4'>
                Get Started
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default OnboardingPage
