import { FC, useMemo, useState } from 'react'
import Utils, { planNames } from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import BareButton from 'components/base/forms/BareButton'
import { Req } from 'common/types/requests'
import UsageBillingPrototype from './UsageBillingPrototype'
import UsageNotifications from './UsageNotifications'
import usePrototypeUsage from './usePrototypeUsage'
import { ScenarioId, SCENARIOS } from './fixtures'
import { UsageNotification } from './types'
import './UsageBillingPrototype.scss'

type UsageBillingPrototypePageProps = {
  organisationId: number
}

type Tab = 'usage' | 'notifications'

const TABS: { id: Tab; label: string }[] = [
  { id: 'usage', label: 'Usage' },
  { id: 'notifications', label: 'Notifications' },
]

/**
 * PROTOTYPE (#8184). Wiring for the prototype: which scenario, which tab, and
 * where the data comes from. Reached only when the `usage_billing_prototype`
 * flag is on.
 */
const UsageBillingPrototypePage: FC<UsageBillingPrototypePageProps> = ({
  organisationId,
}) => {
  const [scenario, setScenario] = useState<ScenarioId>('healthy')
  const [tab, setTab] = useState<Tab>('usage')
  const [project, setProject] = useState<string | undefined>()

  const currentPlan = Utils.getPlanName(AccountStore.getActiveOrgPlan())
  const orgSubscription = AccountStore.getOrganisation()?.subscription
  const isOnFreePlanPeriods =
    planNames.free === currentPlan ||
    !orgSubscription?.has_active_billing_periods

  const [billingPeriod, setBillingPeriod] = useState<
    Req['getOrganisationUsage']['billing_period']
  >(isOnFreePlanPeriods ? '90_day_period' : 'current_billing_period')

  // Notifications live here rather than in the settings screen, so removing
  // one takes its marker off the meter. Null until edited, so switching
  // scenario shows that fixture's own notifications again.
  const [editedNotifications, setEditedNotifications] = useState<
    UsageNotification[] | null
  >(null)

  const baseView = usePrototypeUsage({
    billingPeriod,
    isOnFreePlanPeriods,
    organisationId,
    // ProjectFilter hands back the id as a string, the query wants the pk.
    projectId: project ? Number(project) : undefined,
    scenario,
  })

  const view = useMemo(
    () =>
      editedNotifications
        ? { ...baseView, notifications: editedNotifications }
        : baseView,
    [baseView, editedNotifications],
  )

  return (
    <div className='px-3 px-md-4 pt-4 pb-4'>
      <div className='usage-proto__switch'>
        <div
          className='usage-proto__switch-group'
          role='group'
          aria-label='Prototype state'
        >
          <span className='usage-proto__sub'>Prototype state</span>
          {SCENARIOS.map((option) => (
            <BareButton
              key={option.id}
              onClick={() => {
                setScenario(option.id)
                setEditedNotifications(null)
              }}
              aria-pressed={option.id === scenario}
              className={
                option.id === scenario
                  ? 'usage-proto__switch-btn usage-proto__switch-btn--active'
                  : 'usage-proto__switch-btn'
              }
            >
              {option.label}
            </BareButton>
          ))}
        </div>
        <div
          className='usage-proto__switch-group'
          role='group'
          aria-label='Screen'
        >
          {TABS.map((option) => (
            <BareButton
              key={option.id}
              onClick={() => setTab(option.id)}
              aria-pressed={tab === option.id}
              className={
                tab === option.id
                  ? 'usage-proto__switch-btn usage-proto__switch-btn--active'
                  : 'usage-proto__switch-btn'
              }
            >
              {option.label}
            </BareButton>
          ))}
        </div>
      </div>

      {tab === 'usage' ? (
        <UsageBillingPrototype
          view={view}
          organisationId={organisationId}
          project={project}
          setProject={setProject}
          // Fixtures do not re-query, so the selector follows the fixture
          // rather than contradicting the period shown underneath it.
          billingPeriod={
            scenario === 'live' ? billingPeriod : view.period.selectValue
          }
          setBillingPeriod={setBillingPeriod}
        />
      ) : (
        <UsageNotifications
          notifications={view.notifications}
          onChange={setEditedNotifications}
          channels={view.channels}
        />
      )}
    </div>
  )
}

export default UsageBillingPrototypePage
