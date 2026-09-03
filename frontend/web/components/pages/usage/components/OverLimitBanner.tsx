import { FC } from 'react'
import Constants from 'common/constants'
import { Button } from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import {
  overLimitBannerCopy,
  OverLimit,
} from 'components/pages/usage/overLimit'
import { UsageBasis } from 'components/pages/usage/utils'

export type OverLimitBannerProps = {
  over: OverLimit
  basis: UsageBasis
  canUpgrade?: boolean
  mayBeCharged?: boolean
}

const OverLimitBanner: FC<OverLimitBannerProps> = ({
  basis,
  canUpgrade,
  mayBeCharged,
  over,
}) => {
  const { body, title } = overLimitBannerCopy(over, basis, mayBeCharged)

  return (
    <div
      role='alert'
      className='alert alert-danger d-flex align-items-start gap-3 mb-4'
    >
      <Icon name='close-circle' aria-hidden />
      <div className='flex-fill'>
        <strong className='d-block'>{title}</strong>
        {body}
      </div>
      {canUpgrade && (
        <Button
          className='flex-shrink-0'
          href={Constants.getUpgradeUrl('usage')}
        >
          Upgrade plan
        </Button>
      )}
    </div>
  )
}

export default OverLimitBanner
