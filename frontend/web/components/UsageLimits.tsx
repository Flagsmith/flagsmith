import React from 'react'
import Utils from 'common/utils/utils'
import classNames from 'classnames'

type UsageData = {
  label: string
  value: number
  maxValue: number
}

type UsageLimitsType = {
  usageData: UsageData[]
}

const UsageLimits: React.FC<UsageLimitsType> = ({ usageData }) => {
  return (
    <div className='col-md-10'>
      <h5>Current Project Usage Limits</h5>
      <p className='fs-small lh-sm'>
        In order to ensure consistent performance, Flagsmith has the following
        limitations.{' '}
        <Button
          theme='text'
          href='https://docs.flagsmith.com/system-administration/system-limits'
          target='_blank'
          className='fw-normal'
        >
          Learn about System Limits.
        </Button>
      </p>
      <Row className='justify-content-space-around'>
        {usageData.map((data: UsageData, index: number) => {
          const percentage = Utils.calculateRemainingLimitsPercentage(
            data.value,
            data.maxValue,
          )?.percentage
          return (
            <UsageFormGroup
              key={index}
              label={data.label}
              value={`${data.value}/${data.maxValue}`}
              percentage={percentage}
            />
          )
        })}
      </Row>
    </div>
  )
}

type UsageFormGroupType = {
  label: string
  value: string
}

const UsageFormGroup: React.FC<UsageFormGroupType> = ({
  label,
  percentage,
  value,
}) => {
  return (
    <FormGroup className='m-0'>
      <strong>{label}</strong>

      <p
        className={classNames('centered-container m-0', {
          'text-danger': percentage >= 100,
          'text-warning': percentage >= 90 && percentage <= 99,
        })}
      >
        {value}
      </p>
    </FormGroup>
  )
}

export default UsageLimits
