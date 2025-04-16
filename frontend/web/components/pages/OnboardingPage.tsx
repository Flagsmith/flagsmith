import React, { FC, useEffect, useState } from 'react'
import Logo from 'components/Logo'
import Button from 'components/base/forms/Button'
import { useCreateOnboardingMutation } from 'common/services/useOnboarding'
import { useGetBuildVersionQuery } from 'common/services/useBuildVersion'
import AccountProvider from 'common/providers/AccountProvider'
import OnboardingStep from 'components/onboarding/OnboardingStep'
import OnboardingAccountForm from 'components/onboarding/OnboardingAccountForm'
import OnboardingOrganisationForm from 'components/onboarding/OnboardingOrganisationForm'
import Utils from 'common/utils/utils'

type OnboardingPageProps = {
  onComplete?: () => void
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
    Utils.isValidEmail(onboarding.email) &&
    requirementsMet
  const isStep2Valid = !!onboarding.organisation_name

  const onSubmitStep1 = () => setStep(2)

  return (
    <AccountProvider>
      {(
        {
          error,
          isSaving,
        }: { error?: any; isLoading: boolean; isSaving: boolean },
        { register }: { register: (data: any, isInvite: boolean) => void },
      ) => (
        <div className='position-fixed overflow-auto top-0 bottom-0 left-0 w-100'>
          <div className='min-vh-100 w-100 d-flex flex-1 flex-column justify-content-center align-items-center'>
            <div className='container'>
              {step ? (
                <div className='px-2 d-flex flex-column gap-3'>
                  <div className='text-center'>
                    <Logo size={100} />
                  </div>
                  <OnboardingStep
                    step={1}
                    currentStep={step}
                    title='Your account'
                    description='This account will be set as the superuser for the Django Admin. You will be able to set up SSO and OAuth for your team members.'
                    completedTitle={`Hey, ${onboarding.first_name}!`}
                  >
                    <OnboardingAccountForm
                      onboarding={onboarding}
                      error={error}
                      isValid={isStep1Valid}
                      setFieldValue={setFieldValue}
                      onSubmit={onSubmitStep1}
                      onRequirementsMet={setRequirementsMet}
                    />
                  </OnboardingStep>
                  <OnboardingStep
                    step={2}
                    currentStep={step}
                    title='Your organisation'
                    description='Organisations are a way for you and other team members to manage projects and their features. Users can be members of multiple organisations.'
                    completedTitle={`Creating the organisation ${onboarding.organisation_name}`}
                  >
                    <OnboardingOrganisationForm
                      onboarding={onboarding}
                      error={error}
                      isValid={isStep2Valid}
                      isSaving={isSaving}
                      setFieldValue={setFieldValue}
                      onSubmit={() => {
                        register(onboarding, false)
                      }}
                      onBack={() => setStep(1)}
                    />
                  </OnboardingStep>
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
