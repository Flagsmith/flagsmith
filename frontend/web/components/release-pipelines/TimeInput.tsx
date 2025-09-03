import React, { useEffect, useState } from 'react'
import Input from 'components/base/forms/Input'

import Utils from 'common/utils/utils'
import { TIME_UNIT_OPTIONS, TimeUnit } from './constants'
import moment from 'moment'
import InputGroup from 'components/base/forms/InputGroup'

type TimeUnitType = (typeof TimeUnit)[keyof typeof TimeUnit]

interface TimeIntervalInputProps {
  interval?: string
  title?: string
  onIntervalChange: (interval: string) => void
  className?: string
}

const TimeIntervalInput: React.FC<TimeIntervalInputProps> = ({
  className,
  interval,
  onIntervalChange,
  title,
}) => {
  const existingWaitForTime = Utils.getExistingWaitForTime(interval)

  // These are not fetched directly from stageData because
  // it gives more flexibility to the user to set 24h or 1 day
  const [amountOfTime, setAmountOfTime] = useState(
    existingWaitForTime?.amountOfTime || 1,
  )
  const [selectedTimeUnit, setSelectedTimeUnit] = useState<TimeUnitType>(
    existingWaitForTime?.timeUnit || TimeUnit.DAY,
  )

  function formatDurationToHHMMSS(duration: moment.Duration) {
    const totalSeconds = duration.asSeconds()

    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const seconds = Math.floor(totalSeconds % 60)

    return `${hours}:${String(minutes).padStart(2, '0')}:${String(
      seconds,
    ).padStart(2, '0')}`
  }

  const handleChange = (time: number, unit: TimeUnitType) => {
    setAmountOfTime(time)
    setSelectedTimeUnit(unit)

    const duration = moment.duration(time, unit)
    const formatted = formatDurationToHHMMSS(duration)

    onIntervalChange(formatted)
  }

  useEffect(() => {
    if (!interval) {
      const time = 1
      const unit = TimeUnit.DAY

      return handleChange(time, unit)
    }
  }, [interval])

  return (
    <Row className={`${className} gap-2 align-items-end`}>
      <InputGroup
        title={title}
        value={`${amountOfTime}`}
        inputProps={{
          error: !amountOfTime,
          name: 'amount-of-time',
        }}
        inputClassName='input'
        name='amount-of-time'
        isValid={amountOfTime >= 1}
        min={1}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
          const value = Utils.safeParseEventValue(e)
          handleChange(Number(value), selectedTimeUnit)
        }}
        type='number'
        placeholder='Amount of time'
        className='flex-1 mb-0 flex'
      />

      <div className='w-50'>
        <Select
          value={Utils.toSelectedValue(selectedTimeUnit, TIME_UNIT_OPTIONS)}
          options={TIME_UNIT_OPTIONS}
          onChange={(option: { value: string; label: string }) =>
            handleChange(amountOfTime, option.value as TimeUnit)
          }
        />
      </div>
    </Row>
  )
}

export default TimeIntervalInput
