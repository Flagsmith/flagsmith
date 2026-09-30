import classNames from 'classnames'
import Switch from 'components/Switch'
import Text from 'components/base/Text'

export type PricingToggleProps = {
  isYearly: boolean
  onChange: (isYearly: boolean) => void
}

export const PricingToggle = ({ isYearly, onChange }: PricingToggleProps) => {
  return (
    <div className='d-flex mb-4 font-weight-medium justify-content-center align-items-center gap-2'>
      <Text
        variant='h5'
        level={5}
        className={classNames('mb-0', {
          'text-muted': !isYearly,
        })}
      >
        Pay Yearly & Save
      </Text>
      <Switch
        checked={!isYearly}
        onChange={() => {
          onChange(!isYearly)
        }}
      />
      <Text
        variant='h5'
        level={5}
        className={classNames('mb-0', {
          'text-muted': isYearly,
        })}
      >
        Pay Monthly
      </Text>
    </div>
  )
}
