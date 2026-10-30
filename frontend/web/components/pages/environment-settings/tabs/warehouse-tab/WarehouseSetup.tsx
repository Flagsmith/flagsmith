import { FC, ReactNode, useState } from 'react'
import Icon from 'components/icons/Icon'
import Button from 'components/base/forms/Button'
import AccountStore from 'common/stores/account-store'
import Utils from 'common/utils/utils'
import PlanBasedBanner from 'components/PlanBasedAccess'
import { ConfigFormData } from './ConfigForm'
import SelectableCard from 'components/base/SelectableCard'
import ConfigForm from './ConfigForm'
import ClickHouseConfigForm from './ClickHouseConfigForm'
import WarehouseSqlSnippet from './WarehouseSqlSnippet'
import WarehouseSetupSteps from './WarehouseSetupSteps'
import { getClickHouseOnboardingSql } from './clickhouseSetupSql'
import { ClickHouseFormData } from './clickhouseConfig'
import DatabricksConfigForm from './DatabricksConfigForm'
import { getDatabricksSetupSql } from './databricksSetupSql'
import { DatabricksFormData } from './databricksConfig'
import {
  getMinimumPlans,
  getPlanAvailabilityMessage,
  getWarehouseMinimumPlan,
  getWarehouseTypeStatus,
  WAREHOUSES_FLAG,
  WarehouseTypeOption,
  WarehouseTypeStatus,
} from './warehouseTypes'
import './WarehouseSetup.scss'

type WarehouseSetupProps = {
  environmentId: string
  onEnableFlagsmith: () => void
  onEnableFlagsmithDatabase: () => void
  onCreateSnowflake: (data: ConfigFormData) => Promise<unknown>
  onCreateClickHouse: (data: ClickHouseFormData) => Promise<unknown>
  onCreateDatabricks: (data: DatabricksFormData) => Promise<unknown>
  isCreating: boolean
}

type WarehouseTypeCard = {
  description: string
  icon: ReactNode
  title: string
  type: WarehouseTypeOption
}

const FLAGSMITH_ICON = (
  <img
    src='/static/images/nav-logo.png'
    alt='Flagsmith'
    width={20}
    height={20}
  />
)

const WAREHOUSE_TYPE_CARDS: WarehouseTypeCard[] = [
  {
    description: 'Managed warehouse',
    icon: FLAGSMITH_ICON,
    title: 'Flagsmith',
    type: 'flagsmith',
  },
  {
    description: "Your installation's PostgreSQL",
    icon: FLAGSMITH_ICON,
    title: 'Flagsmith database',
    type: 'flagsmith_database',
  },
  {
    description: 'Open-source OLAP database',
    icon: <Icon name='layers' width={20} />,
    title: 'ClickHouse',
    type: 'clickhouse',
  },
  {
    description: 'Cloud data warehouse',
    icon: <Icon name='flash' width={20} />,
    title: 'Snowflake',
    type: 'snowflake',
  },
  {
    description: 'Google Cloud data warehouse',
    icon: <Icon name='layers' width={20} />,
    title: 'BigQuery',
    type: 'bigquery',
  },
  {
    description: 'Unified analytics platform',
    icon: <Icon name='layers' width={20} />,
    title: 'Databricks',
    type: 'databricks',
  },
]

const STATUS_ORDER: Record<WarehouseTypeStatus, number> = {
  'available': 0,
  'coming-soon': 2,
  'plan-gated': 1,
}

const WarehouseSetup: FC<WarehouseSetupProps> = ({
  environmentId,
  isCreating,
  onCreateClickHouse,
  onCreateDatabricks,
  onCreateSnowflake,
  onEnableFlagsmith,
  onEnableFlagsmithDatabase,
}) => {
  const isSaas = !!Utils.isSaas()
  const minimumPlans = getMinimumPlans({
    enabled: Utils.getFlagsmithHasFeature(WAREHOUSES_FLAG),
    value: Utils.getFlagsmithValue(WAREHOUSES_FLAG),
  })
  const gate = {
    isSaas,
    minimumPlans,
    planId: AccountStore.getActiveOrgPlan(),
  }
  const statusOf = (type: WarehouseTypeOption) =>
    getWarehouseTypeStatus(type, gate)
  const typeCards = WAREHOUSE_TYPE_CARDS.filter(
    ({ type }) => type !== (isSaas ? 'flagsmith_database' : 'flagsmith'),
  ).sort(
    (a, b) => STATUS_ORDER[statusOf(a.type)] - STATUS_ORDER[statusOf(b.type)],
  )
  const [chosenType, setSelectedType] = useState<WarehouseTypeOption>()
  const selectedType = chosenType ?? typeCards[0].type
  const selectedStatus = statusOf(selectedType)
  const selectedMinimumPlan = getWarehouseMinimumPlan(
    selectedType,
    minimumPlans,
  )
  const activeType = selectedStatus === 'available' ? selectedType : undefined

  return (
    <div className='warehouse-setup'>
      <div>
        <h5 className='mb-2'>Warehouse Type</h5>
        <div className='warehouse-setup__type-row'>
          {typeCards.map(({ description, icon, title, type }) => {
            const status = statusOf(type)
            const comingSoon = status === 'coming-soon'
            return (
              <div key={type} className='warehouse-setup__type-card'>
                <SelectableCard
                  icon={icon}
                  title={title}
                  description={description}
                  selected={selectedType === type}
                  onClick={() => !comingSoon && setSelectedType(type)}
                  disabled={comingSoon}
                />
                {comingSoon && (
                  <span className='warehouse-setup__type-badge warehouse-setup__coming-soon fs-captionXSmall'>
                    Coming Soon
                  </span>
                )}
                {status === 'plan-gated' && (
                  <div className='warehouse-setup__type-badge pe-none'>
                    <PlanBasedBanner
                      feature='WAREHOUSE'
                      theme='badge'
                      requiredPlan={getWarehouseMinimumPlan(type, minimumPlans)}
                      badgeAsLink={false}
                    />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {activeType === 'flagsmith' && (
        <div className='warehouse-setup__flagsmith-card'>
          <p className='warehouse-setup__flagsmith-description'>
            Flagsmith manages and hosts the data warehouse for your environment,
            no configuration required.
          </p>
          <div>
            <Button
              id='warehouse-enable'
              theme='primary'
              size='small'
              disabled={isCreating}
              onClick={onEnableFlagsmith}
            >
              {isCreating ? 'Enabling...' : 'Enable'}
            </Button>
          </div>
        </div>
      )}

      {activeType === 'flagsmith_database' && (
        <div className='warehouse-setup__flagsmith-card'>
          <div>
            <p className='warehouse-setup__flagsmith-description mb-2'>
              Flagsmith stores events in its own PostgreSQL database, no
              configuration required.
            </p>
            <p className='text-muted mb-1'>
              Events go to a separate <code>flagsmith_exp</code> schema in the
              database this Flagsmith installation already runs on, so there is
              nothing extra to host or secure.
            </p>
            <p className='text-muted mb-0'>
              This suits most installations. For very high event volumes,
              connect a dedicated warehouse such as ClickHouse or Databricks.
            </p>
          </div>
          <div>
            <Button
              id='warehouse-enable-flagsmith-database'
              theme='primary'
              size='small'
              disabled={isCreating}
              onClick={onEnableFlagsmithDatabase}
            >
              {isCreating ? 'Enabling...' : 'Enable'}
            </Button>
          </div>
        </div>
      )}

      {activeType === 'snowflake' && (
        <ConfigForm
          onSave={onCreateSnowflake}
          onCancel={() => setSelectedType(undefined)}
        />
      )}

      {activeType === 'clickhouse' && (
        <WarehouseSetupSteps
          configure={
            <>
              <p className='text-muted mb-3'>
                Run this once against your ClickHouse instance using an
                administrative user. Replace {'<USER>'} and{' '}
                {'<CHANGE_ME_PASSWORD>'} with your own values.
              </p>
              <WarehouseSqlSnippet sql={getClickHouseOnboardingSql()} />
            </>
          }
          connectDescription='Enter the connection details for the user you created in step 1.'
        >
          <ClickHouseConfigForm
            environmentId={environmentId}
            onSave={onCreateClickHouse}
          />
        </WarehouseSetupSteps>
      )}

      {activeType === 'databricks' && (
        <WarehouseSetupSteps
          configure={
            <>
              <ol className='text-muted mb-3'>
                <li>
                  Use a SQL warehouse. Serverless is recommended: it starts in
                  seconds and costs nothing while idle. All-purpose clusters are
                  not supported.
                </li>
                <li>
                  Note the Server hostname and the Warehouse ID (the last part
                  of the HTTP path) from SQL Warehouses › your warehouse ›
                  Connection details.
                </li>
                <li>
                  Create a service principal (Settings › Identity and access ›
                  Service principals › Add new), then generate a secret with the
                  sql scope and copy the client ID and secret. The secret is
                  shown only once.
                </li>
                <li>
                  On the SQL warehouse, open Permissions and give the service
                  principal Can use.
                </li>
              </ol>
              <p className='text-muted mb-3'>
                Run this script in the SQL editor as an admin. It is safe to run
                more than once. Replace {'<CATALOG>'} and {'<CLIENT_ID>'} with
                your own values.
              </p>
              <WarehouseSqlSnippet sql={getDatabricksSetupSql()} />
              <p className='text-muted mb-0'>
                Service principal secrets expire. When you rotate the secret in
                Databricks, update it here too.
              </p>
            </>
          }
          connectDescription='Enter the connection details and the service principal you created in step 1.'
        >
          <DatabricksConfigForm
            environmentId={environmentId}
            onSave={onCreateDatabricks}
          />
        </WarehouseSetupSteps>
      )}

      {selectedStatus === 'plan-gated' && (
        <PlanBasedBanner
          feature='WAREHOUSE'
          theme='description'
          requiredPlan={selectedMinimumPlan}
          title={`${getPlanAvailabilityMessage(selectedMinimumPlan)}.`}
        />
      )}

      {selectedStatus === 'coming-soon' && (
        <div className='warehouse-setup__flagsmith-card'>
          <p className='warehouse-setup__flagsmith-description'>
            Coming soon. This warehouse type is not yet available.
          </p>
        </div>
      )}
    </div>
  )
}

WarehouseSetup.displayName = 'WarehouseSetup'
export default WarehouseSetup
