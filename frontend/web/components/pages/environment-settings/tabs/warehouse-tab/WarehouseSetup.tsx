import { FC, ReactNode, useState } from 'react'
import Icon from 'components/icons/Icon'
import Button from 'components/base/forms/Button'
import { WarehouseType } from 'common/types/responses'
import { ConfigFormData } from './ConfigForm'
import SelectableCard from 'components/base/SelectableCard'
import ConfigForm from './ConfigForm'
import Utils from 'common/utils/utils'
import ClickHouseConfigForm from './ClickHouseConfigForm'
import WarehouseSqlSnippet from './WarehouseSqlSnippet'
import WarehouseSetupSteps from './WarehouseSetupSteps'
import { getClickHouseOnboardingSql } from './clickhouseSetupSql'
import { ClickHouseFormData } from './clickhouseConfig'
import DatabricksConfigForm from './DatabricksConfigForm'
import { getDatabricksSetupSql } from './databricksSetupSql'
import { DatabricksFormData } from './databricksConfig'
import './WarehouseSetup.scss'

type WarehouseSetupProps = {
  environmentId: string
  onEnableFlagsmith: () => void
  onCreateSnowflake: (data: ConfigFormData) => Promise<unknown>
  onCreateClickHouse: (data: ClickHouseFormData) => Promise<unknown>
  onCreateDatabricks: (data: DatabricksFormData) => Promise<unknown>
  isCreating: boolean
}

type WarehouseTypeOption = WarehouseType | 'bigquery'

type WarehouseTypeCard = {
  description: string
  icon: ReactNode
  title: string
  type: WarehouseTypeOption
}

const WAREHOUSE_TYPE_CARDS: WarehouseTypeCard[] = [
  {
    description: 'Managed warehouse',
    icon: (
      <img
        src='/static/images/nav-logo.png'
        alt='Flagsmith'
        width={20}
        height={20}
      />
    ),
    title: 'Flagsmith',
    type: 'flagsmith',
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

const WarehouseSetup: FC<WarehouseSetupProps> = ({
  environmentId,
  isCreating,
  onCreateClickHouse,
  onCreateDatabricks,
  onCreateSnowflake,
  onEnableFlagsmith,
}) => {
  const [selectedType, setSelectedType] =
    useState<WarehouseTypeOption>('flagsmith')
  const clickhouseEnabled = Utils.getFlagsmithHasFeature('clickhouse_warehouse')
  const databricksEnabled = Utils.getFlagsmithHasFeature('databricks_warehouse')
  const configurableTypes: WarehouseTypeOption[] = [
    'flagsmith',
    ...(clickhouseEnabled ? (['clickhouse'] as const) : []),
    ...(databricksEnabled ? (['databricks'] as const) : []),
  ]
  const isEnabled = (type: WarehouseTypeOption) =>
    configurableTypes.includes(type)
  const typeCards = [...WAREHOUSE_TYPE_CARDS].sort(
    (a, b) => Number(isEnabled(b.type)) - Number(isEnabled(a.type)),
  )

  return (
    <div className='warehouse-setup'>
      <div>
        <h5 className='mb-2'>Warehouse Type</h5>
        <div className='warehouse-setup__type-row'>
          {typeCards.map(({ description, icon, title, type }) => {
            const enabled = isEnabled(type)
            return (
              <div key={type} className='warehouse-setup__type-card'>
                <SelectableCard
                  icon={icon}
                  title={title}
                  description={description}
                  selected={selectedType === type}
                  onClick={() => enabled && setSelectedType(type)}
                  disabled={!enabled}
                />
                {!enabled && (
                  <span className='warehouse-setup__coming-soon fs-captionXSmall'>
                    Coming Soon
                  </span>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {selectedType === 'flagsmith' && (
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

      {selectedType === 'snowflake' && (
        <ConfigForm
          onSave={onCreateSnowflake}
          onCancel={() => setSelectedType('flagsmith')}
        />
      )}

      {selectedType === 'clickhouse' && (
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

      {selectedType === 'databricks' && (
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

      {!configurableTypes.includes(selectedType) && (
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
