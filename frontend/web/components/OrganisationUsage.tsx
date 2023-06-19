import Utils from 'common/utils/utils'
import React, { FC, useState } from 'react'
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip as _Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import ProjectFilter from './ProjectFilter'
import EnvironmentSelect from './EnvironmentSelect'
import moment from 'moment'

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
    <div className='col-md-3 text-center mb-4'>
      <h1>{Utils.numberWithCommas(value)}</h1>
      <Row className='justify-content-center'>
        {!!colour && (
          <span
            style={{
              backgroundColor: colour,
              display: 'inline-block',
              height: 20,
              width: 20,
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
  const colours = ['#6633ff', '#00a696', '#f18e7f', '#F6D46E']

  return data?.totals ? (
    <div className='mt-4'>
      {Utils.getFlagsmithHasFeature('usage_filter') && (
        <Row className='mb-5'>
          <strong>Project</strong>
          <div className='mx-2' style={{ width: 200 }}>
            <ProjectFilter
              showAll
              organisationId={organisationId}
              onChange={setProject}
              value={project}
            />
          </div>
          {project && (
            <>
              <strong className='ml-2'>Environment</strong>
              <div className='ml-2' style={{ width: 200 }}>
                <EnvironmentSelect
                  showAll
                  projectId={project}
                  idField={'id'}
                  onChange={setEnvironment}
                  value={environment}
                />
              </div>
            </>
          )}
        </Row>
      )}

      <div className='row'>
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
          value={data.totals.traits}
          title='Traits'
        />
        <LegendItem
          colour={colours[3]}
          value={data.totals.environmentDocument}
          title='Environment Document'
        />
        <LegendItem value={data.totals.total} title='Total API Calls' />
      </div>
      <ResponsiveContainer height={400} width='100%'>
        <BarChart data={data.events_list}>
          <XAxis
            padding={{ left: 30, right: 30 }}
            allowDataOverflow={false}
            dataKey='day'
            interval={0}
            height={120}
            angle={-90}
            textAnchor='end'
            tickFormatter={(v) => moment(v).format('Do MMM')}
          />
          <YAxis allowDataOverflow={false} />
          <_Tooltip labelFormatter={(v) => moment(v).format('Do MMM YYYY')} />
          <Bar dataKey='flags' stackId='a' fill={colours[0]} />
          <Bar dataKey='identities' stackId='a' fill={colours[1]} />
          <Bar dataKey='traits' stackId='a' fill={colours[2]} />
          <Bar
            name='Environment Document'
            dataKey='environment_document'
            stackId='a'
            fill={colours[3]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  ) : (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

export default OrganisationUsage
