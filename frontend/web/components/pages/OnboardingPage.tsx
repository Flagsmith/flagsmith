import React, { FC, FormEvent, useEffect, useState } from 'react'
import Logo from 'components/Logo'
import Button from 'components/base/forms/Button'
import Card from 'components/Card'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import Icon from 'components/Icon'
import Checkbox from 'components/base/forms/Checkbox'
import { useCreateOnboardingMutation } from 'common/services/useOnboarding'
import PasswordRequirements from 'components/PasswordRequirements'
import isFreeEmailDomain from 'common/utils/isFreeEmailDomain'
import { useGetBuildVersionQuery } from 'common/services/useBuildVersion'
import InfoMessage from 'components/InfoMessage'
import { LoginRequest, RegisterRequest } from 'common/types/requests'
import ErrorMessage from 'components/ErrorMessage'
import AccountProvider from 'common/providers/AccountProvider'
import classNames from 'classnames'

type OnboardingPageProps = {
  onComplete?: () => void
}

interface StepProps {
  currentStep: number
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
  currentStep,
  description,
  isValid,
  onSubmit,
  step,
  title,
}) => {
  const isComplete = currentStep > step
  const isActive = currentStep === step
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
        className={classNames(numberClassName, {
          'bg-white bg-body text-primary fw-semibold': !isComplete && isActive,
          'bg-white bg-light200': !isComplete && !isActive,
        })}
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

const OnboardingPage: FC<OnboardingPageProps> = ({ onComplete }) => {
  const { data: version } = useGetBuildVersionQuery({})
  const [step, setStep] = useState(0)
  const [requirementsMet, setRequirementsMet] = useState(false)

  const [onboarding, setOnboarding] = useState({
    confirm_password: '',
    contact_consent_given: true,
    email: '',
    first_name: '',
    last_name: '',
    organisation_name: '',
    password: '',
    superuser: true,
  })

  useEffect(() => {
    document.body.classList.add('onboarding')
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
  const isValidEmail = Utils.isValidEmail(onboarding.email)
  const isCompanyEmail = !isFreeEmailDomain(onboarding.email)
  return (
    <AccountProvider>
      {(
        {
          error,
          isLoading,
          isSaving,
        }: { error?: any; isLoading: boolean; isSaving: boolean },
        {
          register,
        }: {
          register: (data: RegisterRequest, isInvite: boolean) => void
        },
      ) => (
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
                    currentStep={step}
                    title='Your account'
                    description='This account will be set as the superuser for the Django Admin. You will be able to set up SSO and OAuth for your team members.'
                    completedTitle={`Hey, ${onboarding.first_name}!`}
                    onSubmit={onSubmitStep1}
                    isValid={isStep1Valid}
                  >
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
                        onChange={(e: FormEvent) =>
                          setFieldValue('first_name', e)
                        }
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
                        onChange={(e: FormEvent) =>
                          setFieldValue('last_name', e)
                        }
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
                          Signing up with a work email makes it easier for
                          co-workers to join your Flagsmith organisation.
                        </InfoMessage>
                      </div>
                    )}
                    <div className='col-md-12'>
                      <InputGroup
                        title='Password'
                        data-test='password'
                        isValid={requirementsMet}
                        inputProps={{
                          className: 'full-width',
                          isValid: requirementsMet,
                          name: 'password',
                        }}
                        onChange={(e: FormEvent) => {
                          setFieldValue('password', e)
                        }}
                        className='mb-0 full-width'
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
                      <Button type='submit' disabled={!isStep1Valid}>
                        Next
                      </Button>
                    </div>
                  </Step>
                  <Step
                    step={2}
                    currentStep={step}
                    title='Your organisation'
                    description='Organisations are a way for you and other team members to manage projects and their features. Users can be members of multiple organisations.'
                    completedTitle={`Creating the organisation ${onboarding.organisation_name}`}
                    onSubmit={() => {
                      register(onboarding, false)
                    }}
                    isValid={isStep2Valid}
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
                            onChange={(e: FormEvent) =>
                              setFieldValue('organisation_name', e)
                            }
                          />
                        </div>
                        {!!isCompanyEmail && (
                          <div className='col-md-12'>
                            <Checkbox
                              label='Opt in to a free technical onboarding call. No strings, just booleans. You won’t be subscribed to any marketing communications.'
                              checked={onboarding.contact_consent_given}
                              onChange={(e) =>
                                setFieldValue('contact_consent_given', e)
                              }
                            />
                          </div>
                        )}
                        <ErrorMessage error={error} />
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
                      </>
                    )}
                  </Step>
                </div>
              ) : (
                <div className='text-center'>
                  <Logo size={100} />
                  <h3 className='fw-semibold mt-2'>Welcome to Flagsmith</h3>
                  <h5 className='fw-normal text-muted'>
                    You've successfully installed Flagsmith v{version?.tag},
                    let's get started!
                  </h5>
                  <Button onClick={() => setStep(1)} className='mt-4'>
                    Get Started
                  </Button>
                </div>
              )}
            </div>

            <hr />
            <div className='text-center mb-4'>
              Unsure about something?
              <br />
              View our{' '}
              <a
                className='text-primary'
                href='https://docs.flagsmith.com/deployment'
                target={'_blank'}
                rel='noreferrer'
              >
                self hosting documentation
              </a>{' '}
              or{' '}
              <a
                className='text-primary'
                target='_blank'
                href='https://www.flagsmith.com/contact-us'
                rel='noreferrer'
              >
                get in touch
              </a>
              .
            </div>
          </div>
        </div>
      )}
    </AccountProvider>
  )
}

export default OnboardingPage
