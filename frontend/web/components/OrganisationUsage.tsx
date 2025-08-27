import Utils, { planNames } from 'common/utils/utils'
import React, { FC, useMemo, useState } from 'react'
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
import { IonIcon } from '@ionic/react'
import { checkmarkSharp } from 'ionicons/icons'
import AccountStore from 'common/stores/account-store'
import { billingPeriods, freePeriods, Req } from 'common/types/requests'
import {
  AggregateUsageDataItem,
  AggregateUsageDataItem as UsageEventItem,
} from 'common/types/responses'

type OrganisationUsageType = {
  organisationId: string
}
type LegendItemType = {
  title: string
  value: number
  selection: string[]
  onChange: (v: string) => void
  colour?: string
}

const LegendItem: FC<LegendItemType> = ({
  colour,
  onChange,
  selection,
  title,
  value,
}) => {
  if (!value) {
    return null
  }
  return (
    <div className='mb-4'>
      <h3 className='mb-2'>{Utils.numberWithCommas(value)}</h3>
      <Row className='cursor-pointer' onClick={() => onChange(title)}>
        {!!colour && (
          <span
            className='text-white text-center'
            style={{
              backgroundColor: colour,
              borderRadius: 2,
              display: 'inline-block',
              height: 16,
              width: 16,
            }}
          >
            {selection.includes(title) && (
              <IonIcon size={'8px'} color='white' icon={checkmarkSharp} />
            )}
          </span>
        )}
        <span className='text-muted ml-2'>{title}</span>
      </Row>
    </div>
  )
}

const OrganisationUsage: FC<OrganisationUsageType> = ({ organisationId }) => {
  const [project, setProject] = useState<string | undefined>()
  const [environment, setEnvironment] = useState<string | undefined>()
  const currentPlan = Utils.getPlanName(AccountStore.getActiveOrgPlan())
  const orgSubscription = AccountStore.getOrganisation()?.subscription
  const isOnFreePlanPeriods =
    planNames.free === currentPlan ||
    !orgSubscription?.has_active_billing_periods
  const [billingPeriod, setBillingPeriod] = useState<
    Req['getOrganisationUsage']['billing_period']
  >(isOnFreePlanPeriods ? '90_day_period' : 'current_billing_period')

  const { data, isError } = useGetOrganisationUsageQuery(
    {
      billing_period: billingPeriod,
      environmentId: environment,
      organisationId,
      projectId: project,
    },
    { skip: !organisationId },
  )

  // Aggregate usage events by date, summing metrics across all client types (user agents)
  const consolidatedDailyUsage = useMemo(() => {
    return Object.values(
      data?.events_list?.reduce((acc, event) => {
        const date = event.day
        if (!acc[date]) {
          acc[date] = {
            day: date,
            environment_document: 0,
            flags: 0,
            identities: 0,
            traits: 0,
          }
        }

        acc[date].flags = (acc[date].flags ?? 0) + (event.flags ?? 0)
        acc[date].identities =
          (acc[date].identities ?? 0) + (event.identities ?? 0)
        acc[date].traits = (acc[date].traits ?? 0) + (event.traits ?? 0)
        acc[date].environment_document =
          (acc[date].environment_document ?? 0) +
          (event.environment_document ?? 0)

        return acc
      }, {} as Record<string, AggregateUsageDataItem>) || {},
    )
  }, [data?.events_list])

  const colours = ['#0AADDF', '#27AB95', '#FF9F43', '#EF4D56']
  const [selection, setSelection] = useState([
    'Flags',
    'Identities',
    'Environment Document',
    'Traits',
  ])
  const updateSelection = (key) => {
    if (selection.includes(key)) {
      setSelection(selection.filter((v) => v !== key))
    } else {
      setSelection(selection.concat([key]))
    }
  }

  return data?.totals || isError ? (
    <div className='mt-4 row'>
      <div className='col-md-4'>
        <label>Period</label>
        <Select
          onChange={(v) => setBillingPeriod(v.value)}
          value={billingPeriods.find((v) => v.value === billingPeriod)}
          options={isOnFreePlanPeriods ? freePeriods : billingPeriods}
        />
      </div>
      <div className='col-md-4 mb-5'>
        <label>Project</label>
        <ProjectFilter
          showAll
          organisationId={parseInt(organisationId)}
          onChange={setProject}
          value={project}
        />
      </div>
      {project && (
        <div className='col-md-4'>
          <label>Environment</label>
          <EnvironmentFilter
            showAll
            projectId={project}
            onChange={setEnvironment}
            value={environment}
          />
        </div>
      )}
      {data?.totals && (
        <div className='d-flex gap-5 align-items-center'>
          <LegendItem
            selection={selection}
            onChange={updateSelection}
            colour={colours[0]}
            value={data.totals.flags}
            title='Flags'
          />
          <LegendItem
            selection={selection}
            onChange={updateSelection}
            colour={colours[1]}
            value={data.totals.identities}
            title='Identities'
          />
          <LegendItem
            selection={selection}
            onChange={updateSelection}
            colour={colours[2]}
            value={data.totals.environmentDocument}
            title='Environment Document'
          />
          <LegendItem
            selection={selection}
            onChange={updateSelection}
            colour={colours[3]}
            value={data.totals.traits}
            title='Traits'
          />
          <LegendItem value={data.totals.total} title='Total API Calls' />
        </div>
      )}
      {isError || data?.events_list?.length === 0 ? (
        <div className='py-4 fw-semibold text-center'>
          {isError
            ? 'Your organisation does not have recurrent billing periods'
            : 'No usage recorded.'}
        </div>
      ) : (
        <ResponsiveContainer height={400} width='100%'>
          <BarChart
            data={consolidatedDailyUsage?.map((v) => {
              return {
                ...v,
                environment_document: selection.includes('Environment Document')
                  ? v.environment_document
                  : undefined,
                flags: selection.includes('Flags') ? v.flags : undefined,
                identities: selection.includes('Identities')
                  ? v.identities
                  : undefined,
                traits: selection.includes('Traits') ? v.traits : undefined,
              }
            })}
            style={{ stroke: '#fff', strokeWidth: 1 }}
          >
            <CartesianGrid stroke='#EFF1F4' vertical={false} />
            <XAxis
              padding='gap'
              allowDataOverflow={false}
              dataKey='day'
              interval={data.events_list?.length > 31 ? 7 : 0}
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
            {selection.includes('Flags') && (
              <Bar dataKey='flags' barSize={14} stackId='a' fill={colours[0]} />
            )}
            {selection.includes('Identities') && (
              <Bar
                dataKey='identities'
                barSize={14}
                stackId='a'
                fill={colours[1]}
              />
            )}
            {selection.includes('Environment Document') && (
              <Bar
                name='Environment Document'
                dataKey='environment_document'
                stackId='a'
                fill={colours[2]}
                barSize={14}
              />
            )}
            {selection.includes('Traits') && (
              <Bar
                dataKey='traits'
                barSize={14}
                stackId='a'
                fill={colours[3]}
              />
            )}
          </BarChart>
        </ResponsiveContainer>
      )}
      <InfoMessage>
        Please be aware that usage data can be delayed by up to 3 hours.
      </InfoMessage>
      <div>
        <h4>What do these numbers mean?</h4>
        <h5>Flags</h5>
        <p>
          This is a single call to get the Environment Flag defaults, without
          providing an Identity. Note that if you trigger an update of flags via
          the SDK, this will count as an additional call.
        </p>
        <p>
          <a
            href='https://docs.flagsmith.com/basic-features/managing-features'
            target='_blank'
            rel='noreferrer'
          >
            Learn more.
          </a>
        </p>
        <h5>Identities</h5>
        <p>
          This is a single call to get the flags for a specific Identity. If
          this is the first time flags have been requested for that Identity, it
          will be persisted in our datastore. Note that this number is{' '}
          <em>not</em> a total count of Identities in the datastore, but the
          number of times an Identity has requested their flags. Note that if
          you trigger an update of flags via the SDK, this will count as an
          additional call.
        </p>
        <p>
          <a
            href='https://docs.flagsmith.com/basic-features/managing-identities'
            target='_blank'
            rel='noreferrer'
          >
            Learn more.
          </a>
        </p>
        <h5>Environment Document</h5>
        <p>
          This is a single call made by Server-Side SDKs (when running in Local
          Evaluation Mode), and the Edge Proxy to get the entire Environment
          dataset so they can run flag evaluations locally.
        </p>
        <p>
          By default, server-side SDKs refresh this data every 60 seconds, and
          the Edge Proxy every 10 seconds. Each refresh will count as a single
          call. These time periods are configurable.
        </p>
        <p>
          <a
            href='https://docs.flagsmith.com/clients/overview#local-evaluation'
            target='_blank'
            rel='noreferrer'
          >
            Learn more.
          </a>
        </p>
        <h5>Traits</h5>
        <p>
          This is the number of times Traits for an Identity have been written.
        </p>
        <p>
          <a
            href='https://docs.flagsmith.com/basic-features/managing-identities'
            target='_blank'
            rel='noreferrer'
          >
            Learn more.
          </a>
        </p>
        <h5>Total API calls</h5>
        <p>This is a sum of the above.</p>
      </div>
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
                    Traits: {Utils.numberWithCommas(payload[dataKey])}
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
                    Flags: {Utils.numberWithCommas(payload[dataKey])}
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
                    Identities: {Utils.numberWithCommas(payload[dataKey])}
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
                    Environment Document:{' '}
                    {Utils.numberWithCommas(payload[dataKey])}
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
