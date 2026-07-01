import { FC, ReactNode } from 'react'
import Button, { themeClassNames } from 'components/base/forms/Button'

type RefreshControlProps = {
  onRefresh: () => void
  isRefreshing: boolean
  disabled: boolean
  disabledReason?: string
  theme?: keyof typeof themeClassNames
  label?: ReactNode
  children?: ReactNode
}

const RefreshControl: FC<RefreshControlProps> = ({
  children,
  disabled,
  disabledReason,
  isRefreshing,
  label,
  onRefresh,
  theme = 'secondary',
}) => (
  <div className='d-flex flex-column align-items-end'>
    <Button
      disabled={disabled}
      isLoading={isRefreshing}
      onClick={onRefresh}
      size='small'
      theme={theme}
      title={disabled && !isRefreshing ? disabledReason : undefined}
    >
      {children ?? 'Refresh'}
    </Button>
    {label ? (
      <div className='text-muted fs-caption mt-1 text-end'>{label}</div>
    ) : null}
  </div>
)

export default RefreshControl
