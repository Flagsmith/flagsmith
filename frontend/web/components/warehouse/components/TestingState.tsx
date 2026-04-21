import React, { FC } from 'react'
import { motion } from 'motion/react'
import Icon from 'components/icons/Icon'
import { staggerContainer, staggerItem } from 'common/utils/motion'
import { TESTING_STEPS } from 'components/warehouse/types'
import './TestingState.scss'

type TestingStateProps = {
  currentStep?: number
}

const TestingState: FC<TestingStateProps> = ({
  currentStep = TESTING_STEPS.length,
}) => {
  return (
    <div className='wh-testing'>
      <div className='wh-testing__spinner'>
        <Icon name='refresh' width={32} />
      </div>
      <span className='wh-testing__title'>Connecting…</span>

      <motion.div
        className='wh-testing__steps'
        variants={staggerContainer(0.6)}
        initial='hidden'
        animate='visible'
      >
        {TESTING_STEPS.map((step, index) => (
          <motion.div
            key={step}
            className={`wh-testing__step ${
              index < currentStep ? 'wh-testing__step--done' : ''
            }`}
            variants={staggerItem}
          >
            {index < currentStep ? (
              <Icon name='checkmark-circle' width={16} />
            ) : (
              <span className='wh-testing__step-dot' />
            )}
            <span>{step}</span>
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}

TestingState.displayName = 'WarehouseTestingState'
export default TestingState
