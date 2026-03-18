import React from 'react'
import Icon from 'components/Icon'
import { PRIMARY_ICON_COLOR } from './constants'
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
            <span>
              <Icon
                name='checkmark-circle'
                fill={feature.iconFill || PRIMARY_ICON_COLOR}
              />
            </span>
            <div className='ml-2'>{feature.text}</div>
          </Row>
        </li>
      ))}
    </ul>
  )
}
