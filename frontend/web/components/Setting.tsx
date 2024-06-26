import React, { FC, ReactNode } from 'react'
import Utils, { PaidFeature } from 'common/utils/utils'
import Switch from './Switch'
import classNames from 'classnames'
import PlanBasedBanner, { featureDescriptions } from './PlanBasedAccess'

type PlanBasedAccessSettingType = {
  feature?: PaidFeature
  disabled?: boolean
  checked: boolean
  onChange: (newValue: boolean) => void
  title?: ReactNode
  description?: ReactNode
  className?: string
}

const Setting: FC<PlanBasedAccessSettingType> = ({
  checked,
  className,
  description,
  disabled,
  feature,
  onChange,
  title,
}) => {
  const hasPlan = !feature || Utils.getPlansPermission(feature)

  return (
    <>
      <Row className={className}>
        <Switch
          disabled={disabled || !hasPlan}
          checked={checked}
          onChange={onChange}
        />
        <h5 className={'mb-0 d-flex gap-2 align-items-center ml-3'}>
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
        <p className={classNames('fs-small lh-sm', { 'opacity-50': !hasPlan })}>
          {featureDescriptions[feature].description}
        </p>
      ) : (
        <p className='fs-small lh-sm'>{description}</p>
      )}
      {!!feature && (
        <>
          <hr />
        </>
      )}
    </>
  )
}

export default Setting
