import React, { FC, useState } from 'react'
import { sortBy } from 'lodash'
import Color from 'color'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import InfoMessage from './InfoMessage'
import EnvironmentTagSelect from './EnvironmentTagSelect'
import { useGetFeatureAnalyticsQuery } from 'common/services/useFeatureAnalytics'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import Utils from 'common/utils/utils'

type FlagAnalyticsType = {
  projectId: string
  featureId: string
  defaultEnvironmentIds: string[]
}

const FlagAnalytics: FC<FlagAnalyticsType> = ({
  defaultEnvironmentIds,
  featureId,
  projectId,
}) => {
  const [environmentIds, setEnvironmentIds] = useState(defaultEnvironmentIds)
  const { data, isLoading } = useGetFeatureAnalyticsQuery(
    {
      environment_ids: environmentIds,
      feature_id: featureId,
      period: 30,
      project_id: projectId,
    },
    {
      skip: !environmentIds?.length || !featureId || !projectId,
    },
  )
  const { data: environments } = useGetEnvironmentsQuery({
    projectId: `${projectId}`,
  })

  return (
    <>
      <FormGroup className='mb-4'>
        <h6 className='mb-2'>Flag events for last 30 days</h6>
        <EnvironmentTagSelect
          projectId={projectId}
          idField='id'
          value={environmentIds}
          multiple
          onChange={setEnvironmentIds as any}
        />
        {isLoading && (
          <div className='text-center'>
            <Loader />
          </div>
        )}
        {data && Array.isArray(data) && data.length > 0 && (
          <div>
            <ResponsiveContainer height={400} width='100%' className='mt-4'>
              <BarChart data={data}>
                <CartesianGrid strokeDasharray='3 5' strokeOpacity={0.4} />
                <XAxis
                  dataKey='day'
                  padding='gap'
                  interval={0}
                  height={100}
                  angle={-90}
                  textAnchor='end'
                  tick={{ dx: -4, fill: '#656D7B' }}
                  tickLine={false}
                  axisLine={{ stroke: '#656D7B' }}
                />
                <YAxis
                  tick={{ fill: '#656D7B' }}
                  axisLine={{ stroke: '#656D7B' }}
                />
                <Tooltip cursor={{ fill: 'transparent' }} />
                {sortBy(environmentIds, (id) =>
                  environments?.results?.findIndex((env) => `${env.id}` === id),
                ).map((id) => {
                  let index = environments?.results.findIndex(
                    (env) => `${env.id}` === id,
                  )
                  if (index === -1) index = 0
                  return (
                    <Bar
                      key={id}
                      dataKey={id}
                      stackId='1'
                      fill={Color(Utils.getTagColour(index)).alpha(0.75).rgb()}
                    />
                  )
                })}
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </FormGroup>
      <InfoMessage>
        The Flag Analytics data will be visible in the Dashboard between 30
        minutes and 1 hour after it has been collected.{' '}
        <a
          target='_blank'
          href='https://docs.flagsmith.com/advanced-use/flag-analytics'
          rel='noreferrer'
        >
          View docs
        </a>
      </InfoMessage>
    </>
  )
}

export default FlagAnalytics
