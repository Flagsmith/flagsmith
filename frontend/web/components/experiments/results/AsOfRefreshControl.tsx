import { FC } from 'react'
import moment from 'moment'
import Button from 'components/base/forms/Button'

type AsOfRefreshControlProps = {
  asOf: string | null
  isRefreshing: boolean
  disabled: boolean
  disabledReason?: string
  onRefresh: () => void
}

export const AsOfLabel: FC<{ asOf: string | null }> = ({ asOf }) => (
  <span className='text-muted fs-caption'>
    {asOf ? `As of ${moment.utc(asOf).format('D MMM YYYY, HH:mm')} UTC` : ''}
  </span>
)

const AsOfRefreshControl: FC<AsOfRefreshControlProps> = ({
  disabled,
  disabledReason,
  isRefreshing,
  onRefresh,
}) => (
  <Button
    disabled={disabled || isRefreshing}
    onClick={onRefresh}
    size='small'
    theme='secondary'
    title={disabled ? disabledReason : undefined}
  >
    {isRefreshing ? 'Refreshing…' : 'Refresh'}
  </Button>
)

export default AsOfRefreshControl
