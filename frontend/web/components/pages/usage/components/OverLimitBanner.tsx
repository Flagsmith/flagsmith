import { FC } from 'react'
import Constants from 'common/constants'
import { Button } from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import {
  BannerContext,
  overLimitBannerCopy,
  restrictedBannerCopy,
} from 'components/pages/usage/copy'
import { OverLimit } from 'components/pages/usage/overLimit'
import { UsageBasis } from 'components/pages/usage/utils'

export type OverLimitBannerProps = BannerContext & {
  /** Admin access has already been cut off. */
  isRestricted?: boolean
  /** Absent while restricted but back under the limit. */
  over?: OverLimit
  basis: UsageBasis
  canUpgrade?: boolean
}

const OverLimitBanner: FC<OverLimitBannerProps> = ({
  basis,
  canUpgrade,
  isRestricted,
  mayBeCharged,
  over,
}) => {
  const copy = isRestricted
    ? restrictedBannerCopy(over)
    : over && overLimitBannerCopy(over, basis, { mayBeCharged })

  if (!copy) {
    return null
  }

  const { body, title } = copy

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
