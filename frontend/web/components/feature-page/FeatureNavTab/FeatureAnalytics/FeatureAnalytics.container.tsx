import InfoMessage from 'components/InfoMessage'
import React from 'react'
import FeatureAnalyticsChart from './components/FeatureAnalyticsChart'

export interface FlagAnalyticsData {
  day: string
  count: number
}

interface FeatureAnalyticsProps {
  usageData?: FlagAnalyticsData[]
}

const FeatureAnalytics: React.FC<FeatureAnalyticsProps> = ({ usageData }) => {
  return (
    <>
      <FormGroup>
        {!!usageData && <h5 className='mb-2'>Flag events for last 30 days</h5>}
        {!usageData && (
          <div className='text-center'>
            <Loader />
          </div>
        )}
        <FeatureAnalyticsChart usageData={usageData} />
      </FormGroup>
      <InfoMessage>
        The Flag Analytics data will be visible in the Dashboard between 30
        minutes and 1 hour after it has been collected.{' '}
        <a
          target='_blank'
          href='https://docs.flagsmith.com/advanced-use/flag-analytics'
          rel='noreferrer'
        >
          View docs
        </a>
      </InfoMessage>
    </>
  )
}

export default FeatureAnalytics
