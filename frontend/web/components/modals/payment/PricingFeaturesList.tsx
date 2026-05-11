import React from 'react'
import Icon from 'components/icons/Icon'
import { PricingFeature } from './types'

export type PricingFeaturesListProps = {
  features: PricingFeature[]
  iconClass?: string
}

export const PricingFeaturesList = ({
  features,
  iconClass = 'text-success',
}: PricingFeaturesListProps) => {
  return (
    <ul className='pricing-features mb-0 px-2'>
      {features.map((feature, index) => (
        <li key={index}>
          <Row className='mb-3 pricing-features-item'>
            <span className={iconClass}>
              <Icon name='checkmark-circle' />
            </span>
            <div className='ml-2'>{feature.text}</div>
          </Row>
        </li>
      ))}
    </ul>
  )
}
