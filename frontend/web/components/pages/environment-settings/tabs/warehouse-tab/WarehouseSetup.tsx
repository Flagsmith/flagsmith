import { FC, useState } from 'react'
import Icon from 'components/icons/Icon'
import Button from 'components/base/forms/Button'
import { WarehouseType } from 'common/types/responses'
import { ConfigFormData } from './ConfigForm'
import SelectableCard from 'components/base/SelectableCard'
import ConfigForm from './ConfigForm'
import Utils from 'common/utils/utils'
import ClickHouseConfigForm from './ClickHouseConfigForm'
import { ClickHouseFormData } from './clickhouseConfig'
import './WarehouseSetup.scss'

type WarehouseSetupProps = {
  environmentId: string
  onEnableFlagsmith: () => void
  onCreateSnowflake: (data: ConfigFormData) => Promise<unknown>
  onCreateClickHouse: (data: ClickHouseFormData) => Promise<unknown>
  isCreating: boolean
}

type WarehouseTypeOption = WarehouseType | 'bigquery' | 'databricks'

const WarehouseSetup: FC<WarehouseSetupProps> = ({
  environmentId,
  isCreating,
  onCreateClickHouse,
  onCreateSnowflake,
  onEnableFlagsmith,
}) => {
  const [selectedType, setSelectedType] =
    useState<WarehouseTypeOption>('flagsmith')
  const clickhouseEnabled = Utils.getFlagsmithHasFeature('clickhouse_warehouse')
  const configurableTypes: WarehouseTypeOption[] = clickhouseEnabled
    ? ['flagsmith', 'clickhouse']
    : ['flagsmith']

  return (
    <div className='warehouse-setup'>
      <div>
        <h5 className='mb-2'>Warehouse Type</h5>
        <div className='warehouse-setup__type-row'>
          <div className='warehouse-setup__type-card'>
            <SelectableCard
              icon={
                <img
                  src='/static/images/nav-logo.png'
                  alt='Flagsmith'
                  width={20}
                  height={20}
                />
              }
              title='Flagsmith'
              description='Managed warehouse'
              selected={selectedType === 'flagsmith'}
              onClick={() => setSelectedType('flagsmith')}
            />
          </div>
          <div className='warehouse-setup__type-card'>
            <SelectableCard
              icon={<Icon name='layers' width={20} />}
              title='ClickHouse'
              description='Open-source OLAP database'
              selected={selectedType === 'clickhouse'}
              onClick={() => clickhouseEnabled && setSelectedType('clickhouse')}
              disabled={!clickhouseEnabled}
            />
            {!clickhouseEnabled && (
              <span className='warehouse-setup__coming-soon'>Coming Soon</span>
            )}
          </div>
          <div className='warehouse-setup__type-card'>
            <SelectableCard
              icon={<Icon name='flash' width={20} />}
              title='Snowflake'
              description='Cloud data warehouse'
              selected={false}
              onClick={() => {}}
              disabled
            />
            <span className='warehouse-setup__coming-soon'>Coming Soon</span>
          </div>
          <div className='warehouse-setup__type-card'>
            <SelectableCard
              icon={<Icon name='layers' width={20} />}
              title='BigQuery'
              description='Google Cloud data warehouse'
              selected={false}
              onClick={() => {}}
              disabled
            />
            <span className='warehouse-setup__coming-soon'>Coming Soon</span>
          </div>
          <div className='warehouse-setup__type-card'>
            <SelectableCard
              icon={<Icon name='layers' width={20} />}
              title='Databricks'
              description='Unified analytics platform'
              selected={false}
              onClick={() => {}}
              disabled
            />
            <span className='warehouse-setup__coming-soon'>Coming Soon</span>
          </div>
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
        <ClickHouseConfigForm
          environmentId={environmentId}
          onSave={onCreateClickHouse}
        />
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
