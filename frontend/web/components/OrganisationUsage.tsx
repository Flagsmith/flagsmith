import Utils from 'common/utils/utils'
import React, { FC, useState } from 'react'
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip as _Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  TooltipProps,
} from 'recharts'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import ProjectFilter from './ProjectFilter'
import EnvironmentFilter from './EnvironmentFilter'
import moment from 'moment'
import {
  NameType,
  ValueType,
} from 'recharts/types/component/DefaultTooltipContent'
import InfoMessage from './InfoMessage'

type OrganisationUsageType = {
  organisationId: string
}
type LegendItemType = {
  title: string
  value: number
  colour?: string
}

const LegendItem: FC<LegendItemType> = ({ colour, title, value }) => {
  if (!value) {
    return null
  }
  return (
    <div className='mb-4'>
      <h3 className='mb-2'>{Utils.numberWithCommas(value)}</h3>
      <Row>
        {!!colour && (
          <span
            style={{
              backgroundColor: colour,
              borderRadius: 2,
              display: 'inline-block',
              height: 16,
              width: 16,
            }}
          />
        )}
        <span className='text-muted ml-2'>{title}</span>
      </Row>
    </div>
  )
}

const OrganisationUsage: FC<OrganisationUsageType> = ({ organisationId }) => {
  const [project, setProject] = useState<string | undefined>()
  const [environment, setEnvironment] = useState<string | undefined>()

  const { data } = useGetOrganisationUsageQuery({
    environmentId: environment,
    organisationId,
    projectId: project,
  })
  const colours = ['#0AADDF', '#27AB95', '#FF9F43', '#EF4D56']

  return data?.totals ? (
    <div className='mt-4'>
      <div className='col-md-6 mb-5'>
        <InfoMessage>
          Please be aware that usage data can be delayed by up to 3 hours.
        </InfoMessage>
        <label>Project</label>
        <ProjectFilter
          showAll
          organisationId={organisationId}
          onChange={setProject}
          value={project}
        />
        {project && (
          <div className='mt-4'>
            <label>Environment</label>
            <EnvironmentFilter
              showAll
              projectId={project}
              onChange={setEnvironment}
              value={environment}
            />
          </div>
        )}
      </div>
      <Row style={{ gap: '32px 64px' }}>
        <LegendItem
          colour={colours[0]}
          value={data.totals.flags}
          title='Flags'
        />
        <LegendItem
          colour={colours[1]}
          value={data.totals.identities}
          title='Identities'
        />
        <LegendItem
          colour={colours[2]}
          value={data.totals.environmentDocument}
          title='Environment Document'
        />
        <LegendItem
          colour={colours[3]}
          value={data.totals.traits}
          title='Traits'
        />
        <LegendItem value={data.totals.total} title='Total API Calls' />
      </Row>
      <ResponsiveContainer height={400} width='100%'>
        <BarChart
          data={data.events_list}
          style={{ stroke: '#fff', strokeWidth: 1 }}
        >
          <CartesianGrid stroke='#EFF1F4' vertical={false} />
          <XAxis
            padding='gap'
            allowDataOverflow={false}
            dataKey='day'
            interval={0}
            height={120}
            angle={-90}
            textAnchor='end'
            tickFormatter={(v) => moment(v).format('D MMM')}
            axisLine={{ stroke: '#EFF1F4' }}
            tick={{ dx: -4, fill: '#656D7B' }}
            tickLine={false}
          />
          <YAxis
            allowDataOverflow={false}
            tickLine={false}
            axisLine={{ stroke: '#EFF1F4' }}
            tick={{ fill: '#1A2634' }}
          />
          <_Tooltip
            cursor={{ fill: 'transparent' }}
            content={<RechartsTooltip />}
          />
          <Bar dataKey='flags' barSize={14} stackId='a' fill={colours[0]} />
          <Bar
            dataKey='identities'
            barSize={14}
            stackId='a'
            fill={colours[1]}
          />
          <Bar
            name='Environment Document'
            dataKey='environment_document'
            stackId='a'
            fill={colours[2]}
            barSize={14}
          />
          <Bar dataKey='traits' barSize={14} stackId='a' fill={colours[3]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  ) : (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

const RechartsTooltip: FC<TooltipProps<ValueType, NameType>> = ({
  active,
  label,
  payload,
}) => {
  if (active && payload && payload.length) {
    return (
      <div className='recharts-tooltip py-2'>
        <div className='px-4 py-2 fs-small lh-sm fw-bold recharts-tooltip-header'>
          {moment(label).format('D MMM')}
        </div>
        <hr className='py-0 my-0 mb-3' />
        {payload.map((el: any) => {
          const { dataKey, fill, payload } = el
          switch (dataKey) {
            case 'traits': {
              return (
                <Row key={dataKey} className='px-4 mb-3'>
                  <span
                    style={{
                      backgroundColor: fill,
                      borderRadius: 2,
                      display: 'inline-block',
                      height: 16,
                      width: 16,
                    }}
                  />
                  <span className='text-muted ml-2'>
                    Traits: {payload[dataKey]}
                  </span>
                </Row>
              )
            }
            case 'flags': {
              return (
                <Row key={dataKey} className='px-4 mb-3'>
                  <span
                    style={{
                      backgroundColor: fill,
                      borderRadius: 2,
                      display: 'inline-block',
                      height: 16,
                      width: 16,
                    }}
                  />
                  <span className='text-muted ml-2'>
                    Flags: {payload[dataKey]}
                  </span>
                </Row>
              )
            }
            case 'identities': {
              return (
                <Row key={dataKey} className='px-4 mb-3'>
                  <span
                    style={{
                      backgroundColor: fill,
                      borderRadius: 2,
                      display: 'inline-block',
                      height: 16,
                      width: 16,
                    }}
                  />
                  <span className='text-muted ml-2'>
                    Identities: {payload[dataKey]}
                  </span>
                </Row>
              )
            }
            case 'environment_document': {
              return (
                <Row key={dataKey} className='px-4 mb-3'>
                  <span
                    style={{
                      backgroundColor: fill,
                      borderRadius: 2,
                      display: 'inline-block',
                      height: 16,
                      width: 16,
                    }}
                  />
                  <span className='text-muted ml-2'>
                    Environment Document: {payload[dataKey]}
                  </span>
                </Row>
              )
            }
            default: {
              return null
            }
          }
        })}
      </div>
    )
  }

  return null
}

export default OrganisationUsage
