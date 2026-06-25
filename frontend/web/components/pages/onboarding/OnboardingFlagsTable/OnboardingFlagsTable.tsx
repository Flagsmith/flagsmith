import React, { FC } from 'react'
import classNames from 'classnames'
import { Tag as TTag } from 'common/types/responses'
import FeatureName from 'components/feature-summary/FeatureName'
import Tag from 'components/tags/Tag'
import Switch from 'components/Switch'
import './OnboardingFlagsTable.scss'

export type OnboardingFlagsTableStatus = 'waiting' | 'connected'

export type OnboardingFlagRow = {
  name: string
  description?: string
  tags?: Partial<TTag>[]
  enabled: boolean
}

export type OnboardingFlagsTableProps = {
  status: OnboardingFlagsTableStatus
  flags: OnboardingFlagRow[]
  onToggle: (flag: OnboardingFlagRow, enabled: boolean) => void
  // Name of the flag whose toggle is mid-flight, so its Switch disables.
  togglingFlag?: string | null
  // Whether the flag's state has loaded; the toggle stays disabled until then so
  // a click can't no-op against an unresolved feature state. Defaults to true.
  togglesReady?: boolean
}

// The "Your flags" card from the onboarding design: the pre-created flag(s) in a
// real-looking table that reuses the product FeatureName / Tag / Switch. Prop
// driven (the page owns the data and the persisted toggle, see
// useUpdateFeatureStateMutation). `connected` lifts the card with the accent
// border + glow and enables the toggle; `waiting` dims it until the first
// evaluation arrives.
const OnboardingFlagsTable: FC<OnboardingFlagsTableProps> = ({
  flags,
  onToggle,
  status,
  togglesReady = true,
  togglingFlag,
}) => {
  const waiting = status === 'waiting'
  // Toggles are interactive only once the app has connected and the flag state
  // has loaded; before that the table is a dimmed preview and a click would
  // no-op. (A mid-flight toggle also locks its own row, below.)
  const togglesLocked = waiting || !togglesReady
  return (
    <section
      className='onboarding-flags d-flex flex-column align-items-center'
      aria-labelledby='onboarding-flags-title'
    >
      <h3
        className='onboarding-flags__title m-0 fw-bold'
        id='onboarding-flags-title'
      >
        Your flags
      </h3>
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
                  <Tag key={tag.id ?? tag.label} tag={tag} />
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
