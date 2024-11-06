import { FC, useEffect, useState } from 'react'
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
import AccountProvider from 'common/providers/AccountProvider'

type OnboardingPageType = {
  router: RouterChildContext['router']
}

type StepType = {
  value: number
  step: number
  children: React.ReactNode
  completedTitle: React.ReactNode
  title: React.ReactNode
}

const Step: FC<StepType> = ({
  children,
  completedTitle,
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
  if (isActive) {
    return (
      <Card className='rounded position-relative border-1 px-5'>
        <div
          className={`${numberClassName} bg-body text-primary fw-semibold`}
          style={numberStyle}
        >
          {step}
        </div>
        <h5 className='mb-0 text-primary'>{title}</h5>
        {children}
      </Card>
    )
  } else if (isComplete) {
    return (
      <Card className='rounded bg-faint position-relative border-1 px-5'>
        <div
          className={`${numberClassName} bg-success text-white`}
          style={numberStyle}
        >
          <Icon fill='white' name={'checkmark'} />
        </div>
        <h5 className='mb-0 text-success'>{completedTitle}</h5>
      </Card>
    )
  } else {
    return (
      <Card className='rounded position-relative bg-light400 border-1 px-5'>
        <div className={numberClassName} style={numberStyle}>
          {step}
        </div>
        <h5 className='mb-0 text-success'>{title}</h5>
      </Card>
    )
  }
}

const OnboardingPage: FC<OnboardingPageType> = ({ router }) => {
  const [version, setVersion] = useState<Version>()
  const [step, setStep] = useState(0)
  const [organisationName, setOrganisationName] = useState('')

  useEffect(() => {
    getBuildVersion().then((version: Version) => {
      setVersion(version)
    })
  }, [])
  const onSave = (id) => {
    AppActions.selectOrganisation(id)
    API.setCookie('organisation', `${id}`)
    router.history.push(Utils.getOrganisationHomePage(id))
  }
  return (
    <AccountProvider onSave={onSave}>
      {({ isSaving }, { createOrganisation }) => (
        <div className='position-fixed top-0 bottom-0 left-0 w-100'>
          <div className='h-100 w-100 d-flex flex-1 flex-column justify-content-center align-items-center'>
            <div className='container'>
              {step === 0 ? (
                <div className='text-center'>
                  <Logo size={100} />
                  <h3 className='fw-semibold mt-2'>
                    Welcome to Flagsmith {AccountStore.getUser()?.first_name}
                  </h3>
                  <h5 className='fw-normal text-muted'>
                    You've successfully installed Flagsmith v{version?.tag}!
                  </h5>
                  <Button onClick={() => setStep(1)} className='mt-4'>
                    Let's get started
                  </Button>
                </div>
              ) : (
                <div className='px-5 d-flex flex-column gap-4'>
                  <Step
                    step={1}
                    value={step}
                    title='Your organisation'
                    completedTitle={`Creating the organisation ${organisationName}`}
                  >
                    <InputGroup
                      className='mt-2'
                      inputProps={{ autoFocus: true }}
                      title={'Organisation Name'}
                      value={organisationName}
                      onChange={(e) =>
                        setOrganisationName(Utils.safeParseEventValue(e))
                      }
                    />
                    <Button
                      disabled={!organisationName}
                      onClick={() => setStep(2)}
                      className='px-3'
                      size='small'
                    >
                      Next
                    </Button>
                  </Step>
                  <Step step={2} value={step} title='Usage data preferences'>
                    <div className='d-flex mt-4 gap-4'>
                      <Button
                        disabled={!organisationName}
                        onClick={() => setStep(1)}
                        className='px-3'
                        size='small'
                        theme='secondary'
                      >
                        Back
                      </Button>
                      <Button
                        disabled={!organisationName || isSaving}
                        onClick={() => createOrganisation(organisationName)}
                        className='px-3'
                        size='small'
                      >
                        Complete
                      </Button>
                    </div>
                  </Step>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </AccountProvider>
  )
}
export default OnboardingPage
