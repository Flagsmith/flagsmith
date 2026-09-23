import React, { FC } from 'react'
import classNames from 'classnames'
import { Tag as TTag } from 'common/types/responses'
import FeatureName from 'components/feature-summary/FeatureName'
import Tag from 'components/tags/Tag'
import Switch from 'components/Switch'
import Icon from 'components/icons/Icon'
import './OnboardingFlagsTable.scss'

export type OnboardingFlagsTableStatus = 'waiting' | 'connected'

export type OnboardingFlagRow = {
  name: string
  description?: string
  tags?: TTag[]
  enabled: boolean
}

export type OnboardingFlagsTableProps = {
  status: OnboardingFlagsTableStatus
  flags: OnboardingFlagRow[]
  onToggle: (flag: OnboardingFlagRow, enabled: boolean) => void
  togglingFlag?: string | null
  // Defaults true; while false the toggle stays disabled (state not loaded yet).
  togglesReady?: boolean
}

// "Your flags" card: the pre-created flag in a table that reuses the product
// FeatureName / Tag / Switch. Connected lifts it with a glow; waiting dims it.
const OnboardingFlagsTable: FC<OnboardingFlagsTableProps> = ({
  flags,
  onToggle,
  status,
  togglesReady = true,
  togglingFlag,
}) => {
  const waiting = status === 'waiting'
  // Locked until connected and the flag state has loaded (else a click no-ops).
  const togglesLocked = waiting || !togglesReady
  return (
    <section
      className='onboarding-flags d-flex flex-column align-items-center'
      aria-labelledby='onboarding-flags-title'
    >
      <div className='onboarding-flags__heading d-flex align-items-center gap-2'>
        <h3
          className='onboarding-flags__title m-0 fw-bold'
          id='onboarding-flags-title'
        >
          Your flags
        </h3>
        {waiting && (
          <span className='onboarding-flags__hint d-flex align-items-center gap-1'>
            <Icon name='lock' width={13} />
            Flip it once your app connects
          </span>
        )}
      </div>
      <div
        className={classNames(
          'onboarding-flags__table bg-surface-default rounded-xl',
          {
            'onboarding-flags__table--waiting': waiting,
          },
        )}
      >
        <div className='onboarding-flags__head d-flex align-items-center'>
          <span className='onboarding-flags__col onboarding-flags__col--feature'>
            FEATURE
          </span>
          <span className='onboarding-flags__col onboarding-flags__col--enabled'>
            ENABLED
          </span>
        </div>
        {flags.map((flag) => (
          <div
            className='onboarding-flags__row d-flex align-items-center'
            key={flag.name}
          >
            <div className='onboarding-flags__feature d-flex flex-column gap-1'>
              <div className='d-flex align-items-center gap-2'>
                <FeatureName name={flag.name} />
                {flag.tags?.map((tag) => (
                  <Tag key={tag.id} tag={tag} />
                ))}
              </div>
              {flag.description && (
                <p className='onboarding-flags__desc m-0'>{flag.description}</p>
              )}
            </div>
            <div className='onboarding-flags__toggle'>
              <Switch
                checked={flag.enabled}
                disabled={togglesLocked || togglingFlag === flag.name}
                onChange={(enabled) => onToggle(flag, enabled)}
                aria-label={`Toggle ${flag.name}`}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

export default OnboardingFlagsTable
