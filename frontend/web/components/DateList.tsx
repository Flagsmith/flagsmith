import React, { FC, useMemo } from 'react'
import moment from 'moment'
import { PagedResponse } from 'common/types/responses'
import _ from 'lodash'
import Icon from './Icon'
import Paging from './Paging'
import classNames from 'classnames'

type DateListType<T> = {
  items: PagedResponse<T> | undefined
  dateProperty?: keyof T
  renderRow: (item: T, i: number) => JSX.Element
  dateFormat?: string
  isLoading: boolean
  nextPage: () => void
  prevPage: () => void
  goToPage: (page: number) => void
}

function formatDate(date: string) {
  const today = moment().startOf('day')
  const yesterday = moment().subtract(1, 'days').startOf('day')

  if (moment(date).isSame(today, 'd')) {
    return 'Today'
  } else if (moment(date).isSame(yesterday, 'd')) {
    return 'Yesterday'
  } else {
    return moment(date).format('MMM Do, YYYY')
  }
}

const DateList = <T extends { [key: string]: any }>({
  dateFormat = 'YYYY-MM-DD',
  dateProperty = 'created_at' as keyof T,
  goToPage,
  isLoading,
  items,
  nextPage,
  prevPage,
  renderRow,
}: DateListType<T>) => {
  const groupedData = useMemo(() => {
    return _.groupBy(items?.results || [], (item) =>
      moment(item[dateProperty] as unknown as string).format(dateFormat),
    )
  }, [items, dateFormat, dateProperty])

  const groupedItems = Object.entries(groupedData)
  let itemIndex = 0
  return (
    <>
      {groupedItems.map(([date, dateItems], index) => (
        <div key={date}>
          <div
            className={classNames('d-flex gap-2', {
              'align-items-center': !!items?.previous || index > 0,
            })}
          >
            <div className='ps-8 d-flex flex-column gap-1 align-items-center'>
              {(!!items?.previous || index > 0) && (
                <div style={{ height: 15, width: 1 }} className='border-1' />
              )}
              <Icon name='clock' fill='#9DA4AE' />
              <div style={{ height: 15, width: 1 }} className='border-1' />
            </div>
            <div className='text-muted py-1 fs-caption'>{formatDate(date)}</div>
          </div>

          <div className='border-1 rounded'>
            {dateItems.map((item, i) => {
              const isLastItem = i + 1 === dateItems.length
              const inner = renderRow(item, itemIndex)
              itemIndex++
              return (
                <div key={itemIndex}>
                  {inner}
                  {!isLastItem && <hr className='my-0' />}
                </div>
              )
            })}
          </div>
        </div>
      ))}
      {!!items && (
        <Paging
          paging={items}
          isLoading={isLoading}
          nextPage={nextPage}
          prevPage={prevPage}
          goToPage={goToPage}
        />
      )}
    </>
  )
}

export default DateList
