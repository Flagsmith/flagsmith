import { FC, useMemo } from 'react'
import moment from 'moment'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  ReferenceArea,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  colorSurfaceAction,
  colorTextDanger,
  colorTextSecondary,
} from 'common/theme/tokens'
import { UsagePoint } from './types'
import { compact } from './format'

type UsageChartProps = {
  series: UsagePoint[]
  limit: number | null
  /** End-of-period usage at the current run rate, or null when too early. */
  projected: number | null
  daysRemaining: number
}

const ACCENT = colorSurfaceAction
const DANGER = colorTextDanger

type Row = {
  day: string
  cumulative: number | null
  projection: number | null
}

/**
 * Cumulative usage against the plan limit. The limit is drawn as a ceiling,
 * anything above it is shaded as overage, and the run rate continues as a
 * dashed line to the end of the period.
 */
const UsageChart: FC<UsageChartProps> = ({
  daysRemaining,
  limit,
  projected,
  series,
}) => {
  const rows = useMemo<Row[]>(() => {
    const actual: Row[] = series.map((point, index) => ({
      cumulative: point.cumulative,
      day: point.day,
      // Join the two lines at today so there is no visual gap.
      projection:
        index === series.length - 1 && projected ? point.cumulative : null,
    }))

    if (!projected || daysRemaining <= 0 || !series.length) {
      return actual
    }

    const last = series[series.length - 1]
    const step = (projected - last.cumulative) / daysRemaining
    const future: Row[] = Array.from({ length: daysRemaining }).map(
      (_, index) => ({
        cumulative: null,
        day: moment(last.day)
          .add(index + 1, 'days')
          .format('YYYY-MM-DD'),
        projection: Math.round(last.cumulative + step * (index + 1)),
      }),
    )
    return actual.concat(future)
  }, [series, projected, daysRemaining])

  const peak = Math.max(
    limit ?? 0,
    projected ?? 0,
    series[series.length - 1]?.cumulative ?? 0,
  )
  // Headroom above the highest value, so the topmost label has room to render
  // instead of being clipped by the top of the chart.
  const ceiling = peak ? Math.round(peak * 1.08) : 0
  const today = series[series.length - 1]

  return (
    <ResponsiveContainer height={320} width='100%'>
      <ComposedChart data={rows} margin={{ left: 0, right: 16, top: 8 }}>
        <defs>
          <linearGradient id='usageProtoArea' x1='0' x2='0' y1='0' y2='1'>
            <stop offset='0%' stopColor={ACCENT} stopOpacity={0.18} />
            <stop offset='100%' stopColor={ACCENT} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray='3 5'
          strokeOpacity={0.4}
          vertical={false}
        />
        <XAxis
          dataKey='day'
          height={64}
          angle={-90}
          textAnchor='end'
          interval={Math.ceil((rows.length || 1) / 12)}
          tickFormatter={(day: string) => moment(day).format('D MMM')}
          tick={{ dx: -4, fill: colorTextSecondary, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: colorTextSecondary }}
        />
        <YAxis
          // Pin the top to the ceiling so the limit is always in view rather
          // than the series auto-scaling to fill the panel.
          domain={[0, ceiling || 'auto']}
          tick={{ fill: colorTextSecondary, fontSize: 11 }}
          axisLine={{ stroke: colorTextSecondary }}
          tickFormatter={(value: number) => compact(value)}
        />
        <Tooltip
          labelFormatter={(day: string) => moment(day).format('D MMM')}
          formatter={(value: number, name: string) => [
            compact(value),
            name === 'projection' ? 'Projected' : 'Cumulative',
          ]}
        />
        {!!limit && peak > limit && (
          <ReferenceArea
            y1={limit}
            y2={ceiling}
            fill={DANGER}
            fillOpacity={0.08}
            ifOverflow='extendDomain'
          />
        )}
        <Area
          type='monotone'
          dataKey='cumulative'
          stroke={ACCENT}
          strokeWidth={2.5}
          fill='url(#usageProtoArea)'
          dot={false}
          connectNulls={false}
          isAnimationActive={false}
        />
        <Area
          type='monotone'
          dataKey='projection'
          stroke={ACCENT}
          strokeWidth={2}
          strokeDasharray='5 4'
          fill='none'
          dot={false}
          connectNulls
          isAnimationActive={false}
        />
        {!!limit && (
          <ReferenceLine
            y={limit}
            stroke={DANGER}
            strokeWidth={2}
            label={{
              fill: DANGER,
              fontSize: 11,
              position: 'insideTopRight',
              value: `Plan limit · ${compact(limit)}`,
            }}
          />
        )}
        {!!projected && rows.length > 0 && (
          <ReferenceDot
            r={0}
            x={rows[rows.length - 1].day}
            y={projected}
            isFront
            label={{
              fill: ACCENT,
              fontSize: 11,
              offset: 8,
              position: 'top',
              value: `Projected · ${compact(projected)}`,
            }}
          />
        )}
        {today && (
          <ReferenceDot
            r={4}
            fill={ACCENT}
            stroke={colorSurfaceAction}
            strokeWidth={2}
            x={today.day}
            y={today.cumulative}
            isFront
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  )
}

export default UsageChart
