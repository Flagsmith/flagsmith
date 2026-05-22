import { FC, useState } from 'react'
import Icon from 'components/icons/Icon'
import Button from 'components/base/forms/Button'
import { SnowflakeConfig } from 'common/types/responses'
import SelectableCard from './SelectableCard'
import ConfigForm from './ConfigForm'
import './WarehouseSetup.scss'

type WarehouseSetupProps = {
  onEnableFlagsmith: () => void
  onCreateSnowflake: (config: SnowflakeConfig) => Promise<unknown>
  isCreating: boolean
}

type WarehouseTypeOption = 'flagsmith' | 'snowflake' | 'bigquery' | 'databricks'

const WarehouseSetup: FC<WarehouseSetupProps> = ({
  isCreating,
  onCreateSnowflake,
  onEnableFlagsmith,
}) => {
  const [selectedType, setSelectedType] =
    useState<WarehouseTypeOption>('flagsmith')

  return (
    <div className='warehouse-setup'>
      <div>
        <span className='warehouse-setup__section-label'>Warehouse Type</span>
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
              icon={<Icon name='flash' width={20} />}
              title='Snowflake'
              description='Cloud data warehouse'
              selected={selectedType === 'snowflake'}
              onClick={() => setSelectedType('snowflake')}
            />
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
            Flagsmith manages and hosts the data warehouse for your environment
            &mdash; no configuration required.
          </p>
          <div>
            <Button
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
    </div>
  )
}

WarehouseSetup.displayName = 'WarehouseSetup'
export default WarehouseSetup
