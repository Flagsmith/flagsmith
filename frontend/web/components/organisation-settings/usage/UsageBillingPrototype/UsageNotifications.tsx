import { FC, useState } from 'react'
import Switch from 'components/Switch'
import BareButton from 'components/base/forms/BareButton'
import { Button } from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import { colorIconSecondary } from 'common/theme/tokens'
import { UsageNotification } from './types'

type UsageNotificationsProps = {
  notifications: UsageNotification[]
  /** Lifted, so edits reach the meter markers on the usage screen. */
  onChange: (notifications: UsageNotification[]) => void
  channels: { email: boolean; inApp: boolean }
}

const describe = (percent: number): string => {
  if (percent > 100) return 'You are over your plan limit'
  if (percent === 100) return 'You have reached your plan limit'
  return 'Early warning, while there is time to act'
}

const BILLABLE_CALLS = [
  {
    detail: 'Flags fetched for an anonymous visitor.',
    label: 'Flag evaluations',
    op: 'get-flags',
  },
  {
    detail: 'Flags fetched for a known identity, including any traits sent.',
    label: 'Identity flag evaluations',
    op: 'get-identity-flags',
  },
  {
    detail: 'Traits written against an identity.',
    label: 'Trait updates',
    op: 'set-identity-traits',
  },
  {
    detail: 'The whole environment pulled by a server-side SDK on start-up.',
    label: 'Environment bootstrap',
    op: 'get-environment-document',
  },
]

/**
 * PROTOTYPE (#8184). Screen S3. Local state only: the API that stores this
 * does not exist yet, so nothing here is saved.
 */
const UsageNotifications: FC<UsageNotificationsProps> = ({
  channels,
  notifications: rows,
  onChange,
}) => {
  const [inApp, setInApp] = useState(channels.inApp)
  const [email, setEmail] = useState(channels.email)

  const toggleRow = (percent: number) =>
    onChange(
      rows.map((row) =>
        row.percent === percent ? { ...row, enabled: !row.enabled } : row,
      ),
    )

  const removeRow = (percent: number) =>
    onChange(rows.filter((row) => row.percent !== percent))

  const addRow = () => {
    const highest = [...rows].map((row) => row.percent).sort((a, b) => b - a)[0]
    onChange(
      rows.concat({
        enabled: true,
        percent: Math.min((highest ?? 50) + 25, 500),
      }),
    )
  }

  return (
    <div className='usage-proto'>
      <h4 className='usage-proto__title mb-1'>Usage notifications</h4>
      <p className='usage-proto__sub mb-3'>
        Get an email or an in-app alert when you reach a percentage of your plan
        limit. We never cut off your API.
      </p>

      <div className='usage-proto__panel'>
        <div className='usage-proto__panel-head'>
          <strong>Notify me at</strong>
        </div>
        {[...rows]
          .sort((a, b) => a.percent - b.percent)
          .map((row) => (
            <div className='usage-proto__notify-row' key={row.percent}>
              <div>
                <div>{row.percent}% of plan consumed</div>
                <div className='usage-proto__sub'>{describe(row.percent)}</div>
              </div>
              <div className='usage-proto__notify-actions'>
                <Switch
                  checked={row.enabled}
                  onChange={() => toggleRow(row.percent)}
                />
                <BareButton
                  className='usage-proto__remove'
                  aria-label={`Remove the ${row.percent}% notification`}
                  onClick={() => removeRow(row.percent)}
                >
                  <Icon name='trash-2' width={16} fill={colorIconSecondary} />
                </BareButton>
              </div>
            </div>
          ))}
        <BareButton className='usage-proto__add' onClick={addRow}>
          <Icon name='plus' width={16} /> Add notification
        </BareButton>
      </div>

      <div className='usage-proto__panel'>
        <div className='usage-proto__panel-head'>
          <strong>Notify me via</strong>
        </div>
        <div className='usage-proto__notify-row'>
          <div>
            <div>In-app</div>
            <div className='usage-proto__sub'>Shown across the dashboard</div>
          </div>
          <Switch checked={inApp} onChange={() => setInApp(!inApp)} />
        </div>
        <div className='usage-proto__notify-row'>
          <div>
            <div>Email</div>
            <div className='usage-proto__sub'>
              Sent to your organisation admins
            </div>
          </div>
          <Switch checked={email} onChange={() => setEmail(!email)} />
        </div>
      </div>

      <div className='usage-proto__panel'>
        <div className='usage-proto__panel-head'>
          <strong>What counts as an API call?</strong>
          <a
            className='usage-proto__docs'
            href='https://docs.flagsmith.com/system-administration/api-usage'
            target='_blank'
            rel='noreferrer'
          >
            See docs
          </a>
        </div>
        {BILLABLE_CALLS.map((call) => (
          <div className='usage-proto__notify-row' key={call.op}>
            <div>
              <div>{call.label}</div>
              <div className='usage-proto__sub'>{call.op}</div>
            </div>
            <div className='usage-proto__sub usage-proto__call-detail'>
              {call.detail}
            </div>
          </div>
        ))}
      </div>

      <div className='text-right'>
        <Button disabled>Save notifications</Button>
      </div>
    </div>
  )
}

export default UsageNotifications
