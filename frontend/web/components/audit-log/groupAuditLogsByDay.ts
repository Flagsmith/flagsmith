import moment, { Moment } from 'moment'
import { AuditLogItem } from 'common/types/responses'

export type AuditLogDay = {
  key: string
  label: string
  items: AuditLogItem[]
}

const dayLabel = (day: Moment, now: Moment) => {
  const date = day.format(
    day.isSame(now, 'year') ? 'dddd D MMMM' : 'dddd D MMMM YYYY',
  )
  if (day.isSame(now, 'day')) return `Today · ${date}`
  if (day.isSame(now.clone().subtract(1, 'day'), 'day'))
    return `Yesterday · ${date}`
  return date
}

// Groups by the viewer's local day, keeping the API's order.
export const groupAuditLogsByDay = (
  items: AuditLogItem[],
  now: Moment = moment(),
): AuditLogDay[] => {
  const days: AuditLogDay[] = []
  for (const item of items) {
    const day = moment(item.created_date)
    const key = day.format('YYYY-MM-DD')
    const last = days[days.length - 1]
    if (last?.key === key) {
      last.items.push(item)
    } else {
      days.push({ items: [item], key, label: dayLabel(day, now) })
    }
  }
  return days
}
