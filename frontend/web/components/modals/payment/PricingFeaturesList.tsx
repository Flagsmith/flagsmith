import React from 'react'
import Icon from 'components/Icon'
import { PricingFeature } from './types'

export type PricingFeaturesListProps = {
  features: PricingFeature[]
}

export const PricingFeaturesList = ({ features }: PricingFeaturesListProps) => {
  return (
    <ul className='pricing-features mb-0 px-2'>
      {features.map((feature, index) => (
        <li key={index}>
          <Row className='mb-3 pricing-features-item'>
            <span className={feature.iconClass || 'text-success'}>
              <Icon name='checkmark-circle' />
            </span>
            <div className='ml-2'>{feature.text}</div>
          </Row>
        </li>
      ))}
    </ul>
  )
}
