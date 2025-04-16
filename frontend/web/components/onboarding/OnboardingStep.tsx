import React, { FC } from 'react'
import Card from 'components/Card'
import Icon from 'components/Icon'
import classNames from 'classnames'

type StepProps = {
  currentStep: number
  step: number
  children: React.ReactNode
  completedTitle: React.ReactNode
  title: React.ReactNode
  description: React.ReactNode
}

const Step: FC<StepProps> = ({
  children,
  completedTitle,
  currentStep,
  description,
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
      {isActive && <hr />}
      {isActive && children}
    </Card>
  )
}

export default Step
