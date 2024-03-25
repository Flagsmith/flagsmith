import DatePicker from 'react-datepicker'
import Icon from './Icon'
import { useState } from 'react'

const DateSelect = ({ dateFormat, onChange, onSelect, selected, value }) => {
  const [isMonthPicker, setMonthPicker] = useState(false)
  const [isYearPicker, setYearPicker] = useState(false)
  const [isOpen, setOpen] = useState(false)
  return (
    <Flex style={{ position: 'relative' }}>
      <DatePicker
        dateFormat={dateFormat}
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
                setMonthPicker(true)
                if (isMonthPicker) {
                  setYearPicker(true)
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
        onChange={(date, e) => {
          if (date < new Date()) {
            setMonthPicker(false)
            setYearPicker(false)
            onChange(new Date())
          } else {
            onChange(date)
            if (!e) {
              setOpen(false)
            }
            if (isMonthPicker) {
              setMonthPicker(false)
            }
            if (isYearPicker) {
              setYearPicker(false)
            }
          }
        }}
        className='input-lg'
        formatWeekDay={(nameOfDay) => nameOfDay.substr(0, 1)}
        showTimeSelect={!isMonthPicker && !isYearPicker}
        showMonthYearPicker={isMonthPicker}
        showYearPicker={isYearPicker}
        calendarStartDay={1}
        popperPlacement='bottom-end'
        selected={selected}
        value={value}
        timeFormat='HH:mm'
        onInputClick={() => setOpen(true)}
        onClickOutside={(e) => {
          if (e) {
            setOpen(false)
            setMonthPicker(false)
            setYearPicker(false)
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
