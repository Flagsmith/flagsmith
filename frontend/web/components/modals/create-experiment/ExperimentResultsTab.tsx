import React, { FC } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useGetExperimentResultsQuery } from 'common/services/useExperimentResults'
import useChartTheme from 'common/hooks/useChartTheme'

const getVariantColour = (
  variant: string,
  index: number,
  variantColours: string[],
  winnerColour: string,
  winner?: string,
) =>
  variant === winner
    ? winnerColour
    : variantColours[index % variantColours.length]

type ExperimentResultsTabProps = {
  environmentId: string
  featureName: string
}

const ExperimentResultsTab: FC<ExperimentResultsTabProps> = ({
  environmentId,
  featureName,
}) => {
  const chartTheme = useChartTheme()
  const { data, error, isLoading } = useGetExperimentResultsQuery({
    environmentId,
    featureName,
  })

  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  if (error || !data?.variants?.length) {
    return (
      <div className='text-center py-4'>
        Experiment is on-going, data should start appearing as soon as your
        users use it.
      </div>
    )
  }

  const winner = data.statistics?.winner
  const chanceToWinData = data.statistics?.chance_to_win
    ? Object.entries(data.statistics.chance_to_win).map(([variant, value]) => ({
        chance: (value as number) * 100,
        variant,
      }))
    : []

  return (
    <div className='mt-2'>
      {/* Chart 1: Conversion Rate */}
      <div className='mb-4'>
        <h5 className='mb-2'>Conversion Rate (%)</h5>
        <ResponsiveContainer height={300} width='100%'>
          <BarChart data={data.variants}>
            <CartesianGrid stroke={chartTheme.gridStroke} vertical={false} />
            <XAxis
              dataKey='variant'
              tick={{ fill: chartTheme.tickFill }}
              tickLine={false}
              axisLine={{ stroke: chartTheme.axisStroke }}
            />
            <YAxis
              tick={{ fill: chartTheme.tickFill }}
              tickLine={false}
              axisLine={{ stroke: chartTheme.axisStroke }}
            />
            <Tooltip cursor={{ fill: 'transparent' }} />
            <Bar dataKey='conversion_rate' barSize={40}>
              <LabelList
                dataKey='conversion_rate'
                position='top'
                fill={chartTheme.tickFill}
                formatter={(v: number) => `${v.toFixed(1)}%`}
              />
              {data.variants.map(
                (entry: { variant: string }, index: number) => (
                  <Cell
                    key={index}
                    fill={getVariantColour(
                      entry.variant,
                      index,
                      chartTheme.variantColours,
                      chartTheme.winnerColour,
                      winner,
                    )}
                  />
                ),
              )}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Chart 2: Evaluations & Conversions */}
      <div className='mb-4'>
        <h5 className='mb-2'>Evaluations & Conversions</h5>
        <ResponsiveContainer height={300} width='100%'>
          <BarChart data={data.variants}>
            <CartesianGrid stroke={chartTheme.gridStroke} vertical={false} />
            <XAxis
              dataKey='variant'
              tick={{ fill: chartTheme.tickFill }}
              tickLine={false}
              axisLine={{ stroke: chartTheme.axisStroke }}
            />
            <YAxis
              tick={{ fill: chartTheme.tickFill }}
              tickLine={false}
              axisLine={{ stroke: chartTheme.axisStroke }}
            />
            <Tooltip cursor={{ fill: 'transparent' }} />
            <Legend />
            <Bar
              dataKey='evaluations'
              fill={chartTheme.variantColours[0]}
              barSize={40}
            />
            <Bar
              dataKey='conversions'
              fill={chartTheme.winnerColour}
              barSize={40}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Chart 3: Chance to Win */}
      {chanceToWinData.length > 0 && (
        <div className='mb-4'>
          <h5 className='mb-2'>Chance to Win (%)</h5>
          <ResponsiveContainer height={300} width='100%'>
            <PieChart>
              <Pie
                data={chanceToWinData}
                dataKey='chance'
                nameKey='variant'
                cx='50%'
                cy='50%'
                outerRadius={100}
                label={({ chance, variant }) =>
                  `${variant}: ${chance.toFixed(1)}%`
                }
              >
                {chanceToWinData.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={getVariantColour(
                      entry.variant,
                      index,
                      chartTheme.variantColours,
                      chartTheme.winnerColour,
                      winner,
                    )}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Statistics Summary */}
      {data.statistics && (
        <div className='mb-4'>
          <h5 className='mb-2'>Statistics</h5>
          <div className='list-unstyled'>
            {data.statistics.recommendation && (
              <p className='mb-1'>
                <strong>Recommendation:</strong>{' '}
                {data.statistics.recommendation}
              </p>
            )}
            {data.statistics.lift && (
              <p className='mb-1'>
                <strong>Lift:</strong> {data.statistics.lift}
              </p>
            )}
            {data.statistics.p_value !== null &&
              data.statistics.p_value !== undefined && (
                <p className='mb-1'>
                  <strong>P-value:</strong> {data.statistics.p_value}
                </p>
              )}
            {data.statistics.sample_size_warning && (
              <p className='mb-1 text-warning'>
                {data.statistics.sample_size_warning}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ExperimentResultsTab
