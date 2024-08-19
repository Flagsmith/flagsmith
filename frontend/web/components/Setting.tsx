import React, { FC, ReactNode } from 'react'
import Utils, { PaidFeature } from 'common/utils/utils'
import Switch from './Switch'
import classNames from 'classnames'
import PlanBasedBanner, { featureDescriptions } from './PlanBasedAccess'

type PlanBasedAccessSettingType = {
  feature?: PaidFeature
  disabled?: boolean
  checked?: boolean
  onChange?: (newValue: boolean) => void
  title?: ReactNode
  description?: ReactNode
  component?: ReactNode
  'data-test'?: string
}

const Setting: FC<PlanBasedAccessSettingType> = ({
  checked,
  component,
  description,
  disabled,
  feature,
  onChange,
  title,
  ...props
}) => {
  const hasPlan = !feature || Utils.getPlansPermission(feature)

  return (
    <>
      <Row className={'mb-2'}>
        {!component && (
          <div className='me-3'>
            <Switch
              disabled={disabled || !hasPlan}
              checked={checked}
              onChange={onChange}
              {...props}
            />
          </div>
        )}
        <h5 className={'mb-0 d-flex gap-2 align-items-center'}>
          <span
            className={classNames({
              'opacity-50': !hasPlan,
            })}
          >
            {feature ? featureDescriptions[feature].title : title}
          </span>
          {!!feature && <PlanBasedBanner feature={feature} theme={'badge'} />}
        </h5>
      </Row>
      {feature ? (
        <PlanBasedBanner feature={feature} theme={'description'} />
      ) : (
        <p className='fs-small lh-sm'>{description}</p>
      )}
      {!!feature && !!hasPlan && component}
    </>
  )
}

export default Setting
