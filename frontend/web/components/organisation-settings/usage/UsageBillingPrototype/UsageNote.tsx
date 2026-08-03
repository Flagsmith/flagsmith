import { FC } from 'react'
import Icon from 'components/icons/Icon'
import {
  colorTextDanger,
  colorTextSuccess,
  colorTextWarning,
} from 'common/theme/tokens'
import { UsageView } from './types'
import { compact, currency } from './format'

type UsageNoteProps = {
  view: UsageView
  percent: number
}

type Note = { tone: 'success' | 'warning' | 'danger'; text: string }

const ICON_FILL = {
  danger: colorTextDanger,
  success: colorTextSuccess,
  warning: colorTextWarning,
}

/**
 * The one line on the page that draws a conclusion: how far over, what it
 * costs, and what to do about it. Everything else states a number.
 */
const noteFor = (view: UsageView, percent: number): Note | null => {
  const limit = view.limit
  if (!limit) {
    return null
  }
  const over = view.total - limit
  const overPercent = Math.max(percent - 100, 0)

  if (view.restricted) {
    return {
      text: `Flag serving is paused. Reduce usage below ${compact(
        limit,
      )} calls or upgrade to restore service.`,
      tone: 'danger',
    }
  }

  if (view.grace === 'countdown') {
    return {
      text: `Over your limit by ~${compact(
        over,
      )} calls (${overPercent}%). Flag serving pauses in ${
        view.graceDaysLeft ?? 0
      } days unless usage drops back below ${compact(limit)}.`,
      tone: 'warning',
    }
  }

  if (view.grace === 'covering') {
    return {
      text: `Overage this period: ~${compact(
        over,
      )} calls (${overPercent}%). Covered by your grace period this month, so there is no charge.`,
      tone: 'warning',
    }
  }

  if (view.grace === 'used') {
    return {
      text: `Overage this period: ~${compact(over)} calls (${overPercent}%)${
        view.overageCost ? `, estimated ${currency(view.overageCost)}` : ''
      }. Reduce usage or upgrade to avoid further charges.`,
      tone: 'danger',
    }
  }

  if (!view.projected) {
    return null
  }

  const projectedPercent = Math.round((view.projected / limit) * 100)
  const by = view.period.resetsAt
    ? ` by ${view.period.resetsAt}`
    : ' by the end of this window'

  return projectedPercent >= 100
    ? {
        text: `At this rate you will pass your limit${by}, reaching ~${compact(
          view.projected,
        )} calls (${projectedPercent}% of your limit).`,
        tone: 'warning',
      }
    : {
        text: `On track to use ~${compact(
          view.projected,
        )} calls (${projectedPercent}% of your limit)${by}.`,
        tone: 'success',
      }
}

const UsageNote: FC<UsageNoteProps> = ({ percent, view }) => {
  const note = noteFor(view, percent)
  if (!note) {
    return null
  }

  return (
    <div className={`usage-proto__note usage-proto__note--${note.tone}`}>
      <Icon
        name={note.tone === 'success' ? 'checkmark-circle' : 'warning'}
        width={16}
        fill={ICON_FILL[note.tone]}
      />
      <span>{note.text}</span>
    </div>
  )
}

export default UsageNote
