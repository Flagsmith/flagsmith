import { FC, useCallback, useState } from 'react'
import flagsmith from '@flagsmith/flagsmith'
import Button from 'components/base/forms/Button'
import MetricsComparisonTable from 'components/experiments/MetricsComparisonTable'
import MetricsTrendChart from 'components/experiments/MetricsTrendChart'
import { MOCK_METRICS, MOCK_TRENDS } from './mockData'
import './ExperimentsFakeDoor.scss'

const TRAIT_KEY = 'experimentation_beta'

const ExperimentsFakeDoor: FC = () => {
  const [signedUp, setSignedUp] = useState(
    () => flagsmith.getTrait(TRAIT_KEY) === true,
  )

  const handleSignUp = useCallback(() => {
    const user = AccountStore.getUser()
    const organisation = AccountStore.getOrganisation()
    const name = `${user?.first_name ?? ''} ${user?.last_name ?? ''}`.trim()
    API.trackEvent({
      category: 'experiments',
      event: 'experiments_beta_signup',
      extra: {
        email: user?.email,
        name,
        organisation: organisation?.name,
      },
    })
    flagsmith.trackEvent('experiments_beta_signup', {
      metadata: {
        email: user?.email,
        organisation: organisation?.name,
      },
    })
    flagsmith.setTrait(TRAIT_KEY, true).then(() => {
      setSignedUp(true)
    })
  }, [])

  return (
    <div className='experiments-fake-door'>
      <div className='experiments-fake-door__cta'>
        <div className='experiments-fake-door__cta-content'>
          <span className='experiments-fake-door__cta-title'>
            I would like to participate in beta testing
          </span>
          <span className='experiments-fake-door__cta-subtitle'>
            Get early access to Experiments and help shape the feature.{' '}
            <a
              href='https://docs.flagsmith.com/experiment-statistics'
              target='_blank'
              rel='noreferrer'
            >
              Learn more
            </a>
          </span>
        </div>
        {signedUp ? (
          <span className='experiments-fake-door__cta-thanks'>
            Thank you! 🎉
          </span>
        ) : (
          <Button theme='tertiary' onClick={handleSignUp}>
            Sign Up
          </Button>
        )}
      </div>

      <div className='experiments-fake-door__preview'>
        <div>
          <h5 className='experiments-fake-door__section-title'>
            Metrics Comparison
          </h5>
          <MetricsComparisonTable metrics={MOCK_METRICS} />
        </div>

        <div>
          <h5 className='experiments-fake-door__section-title'>
            Trend over time
          </h5>
          <MetricsTrendChart trends={MOCK_TRENDS} />
        </div>
      </div>
    </div>
  )
}

export default ExperimentsFakeDoor
