import DatePicker, { DatePickerProps } from 'react-datepicker'
import Icon from './Icon'
import { useState, FC } from 'react'

export interface DateSelectProps
  extends Pick<DatePickerProps, 'dateFormat' | 'selected'> {
  value?: DatePickerProps['value']
  className?: string
  isValid?: boolean
  onChange?: (
    date: Date | null,
    event?: React.MouseEvent<HTMLElement> | React.KeyboardEvent<HTMLElement>,
  ) => void
}

const DateSelect: FC<DateSelectProps> = ({
  className,
  dateFormat,
  isValid,
  onChange,
  selected,
  value,
}) => {
  const [isMonthPicker, setIsMonthPicker] = useState(false)
  const [isYearPicker, setIsYearPicker] = useState(false)
  const [touched, setTouched] = useState(false)
  const [isOpen, setIsOpen] = useState(false)

  return (
    <Flex style={{ position: 'relative' }}>
      <DatePicker
        className={`input-lg ${className} ${
          !isValid && touched ? 'invalid' : ''
        }`}
        dateFormat={dateFormat}
        onFocus={() => setTouched(true)}
        renderCustomHeader={({
          date,
          decreaseMonth,
          decreaseYear,
          increaseMonth,
          increaseYear,
        }) => (
          <Row className={'justify-content-between react-datepicker-header'}>
            <span
              onClick={() => {
                if (isYearPicker) {
                  decreaseYear()
                } else {
                  decreaseMonth()
                }
              }}
              className='datepicker-header-buttons'
            >
              <Icon name='chevron-left' />
            </span>
            <div
              onClick={() => {
                setIsMonthPicker(true)
                if (isMonthPicker) {
                  setIsYearPicker(true)
                }
              }}
              className='react-datepicker-header-title'
            >
              {isYearPicker ? (
                `${date.getFullYear()}`
              ) : (
                <>
                  {date.toLocaleString('en', { month: 'long' })}{' '}
                  {date.getFullYear()}
                  <Icon name='chevron-down' />
                </>
              )}
            </div>
            <span
              onClick={() => {
                if (isYearPicker) {
                  increaseYear()
                } else {
                  increaseMonth()
                }
              }}
              className='datepicker-header-buttons'
            >
              <Icon name='chevron-right' />
            </span>
          </Row>
        )}
        minDate={new Date()}
        onChange={(date, e): DatePickerProps['onChange'] => {
          if (date === null) {
            setIsMonthPicker(false)
            setIsYearPicker(false)
            onChange?.(null)
            return
          }

          const today = new Date()
          if (date < today) {
            setIsMonthPicker(false)
            setIsYearPicker(false)
            onChange?.(new Date())
            return
          }

          onChange?.(date)
          if (!e) {
            setIsOpen(false)
          }
          if (isMonthPicker) {
            setIsMonthPicker(false)
          }
          if (isYearPicker) {
            setIsYearPicker(false)
          }
        }}
        formatWeekDay={(nameOfDay) => nameOfDay.substr(0, 1)}
        showTimeSelect={!isMonthPicker && !isYearPicker}
        showMonthYearPicker={isMonthPicker}
        showYearPicker={isYearPicker}
        calendarStartDay={1}
        popperPlacement='bottom-end'
        selected={selected}
        value={value}
        timeFormat='HH:mm'
        onInputClick={() => setIsOpen(true)}
        onClickOutside={(e) => {
          if (e) {
            setIsOpen(false)
            setIsMonthPicker(false)
            setIsYearPicker(false)
          }
        }}
        open={isOpen}
      />
      <span className='calendar-icon'>
        <Icon name='calendar' fill={isOpen ? '#1A2634' : '#9DA4AE'} />
      </span>
    </Flex>
  )
}

export default DateSelect
