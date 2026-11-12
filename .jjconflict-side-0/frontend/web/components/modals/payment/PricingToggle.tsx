import classNames from 'classnames'
import Switch from 'components/Switch'

export type PricingToggleProps = {
  isYearly: boolean
  onChange: (isYearly: boolean) => void
}

export const PricingToggle = ({ isYearly, onChange }: PricingToggleProps) => {
  return (
    <div className='d-flex mb-4 font-weight-medium justify-content-center align-items-center gap-2'>
      <h5
        className={classNames('mb-0', {
          'text-muted': !isYearly,
        })}
      >
        Pay Yearly & Save
      </h5>
      <Switch
        checked={!isYearly}
        onChange={() => {
          onChange(!isYearly)
        }}
      />
      <h5
        className={classNames('mb-0', {
          'text-muted': isYearly,
        })}
      >
        Pay Monthly
      </h5>
    </div>
  )
}
