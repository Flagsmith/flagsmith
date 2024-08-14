import React, { FC, ReactNode } from 'react'
import Icon from './Icon'
import Utils, { PaidFeature } from 'common/utils/utils'
import classNames from 'classnames'
import PlanBasedBanner from './PlanBasedAccess'

type SettingsButtonType = {
  onClick: () => void
  children: ReactNode
  content?: ReactNode
  feature?: PaidFeature
}

const SettingsButton: FC<SettingsButtonType> = ({
  children,
  content,
  feature,
  onClick,
}) => {
  const hasPlan = !feature || Utils.getPlansPermission(feature)
  return (
    <>
      <Row>
        <Row
          className={classNames('gap-2 align-items-center mb-2', {
            'cursor-pointer hover-color-primary': hasPlan,
          })}
          onClick={hasPlan ? onClick : undefined}
        >
          <label
            className={classNames('cols-sm-2 control-label mb-0', {
              'cursor-pointer': hasPlan,
              'opacity-50': !hasPlan,
            })}
          >
            {children} <Icon name='setting' width={20} fill={'#656D7B'} />{' '}
          </label>
          {!!feature && <PlanBasedBanner feature={feature} theme={'badge'} />}
        </Row>
      </Row>
      {content}
    </>
  )
}

export default SettingsButton
