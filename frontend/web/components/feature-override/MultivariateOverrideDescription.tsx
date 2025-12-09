import { FC } from 'react'
import FeatureValue from 'components/feature-summary/FeatureValue'
import { FlagsmithValue } from 'common/types/responses'

type MultivariateType = {
  controlValue: FlagsmithValue
}

const Multivariate: FC<MultivariateType> = ({ controlValue }) => {
  return (
    <div className='list-item-subtitle'>
      <span className='flex-row'>
        This feature is being overridden by a % variation in the environment,
        the control value of this feature is{' '}
        <FeatureValue
          className='ml-1 chip--xs'
          includeEmpty
          value={controlValue}
        />
      </span>
    </div>
  )
}

export default Multivariate
