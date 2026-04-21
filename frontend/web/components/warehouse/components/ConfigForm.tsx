import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import Icon from 'components/icons/Icon'
import SelectableCard from 'components/experiments-v2/shared/SelectableCard'
import {
  MOCK_CONFIG,
  WAREHOUSE_TYPES,
  WarehouseConfig,
  WarehouseType,
} from 'components/warehouse/types'
import './ConfigForm.scss'

type ConfigFormProps = {
  /** Commits the config and transitions to the connected state. */
  onConnect: (config: WarehouseConfig) => void
  onCancel: () => void
}

type TestStatus = 'idle' | 'testing' | 'passed' | 'failed'

const ConfigForm: FC<ConfigFormProps> = ({ onCancel, onConnect }) => {
  const [config, setConfig] = useState<WarehouseConfig>(MOCK_CONFIG)
  const [selectedType, setSelectedType] = useState<WarehouseType>('snowflake')
  const [testStatus, setTestStatus] = useState<TestStatus>('idle')

  const updateField = (field: keyof WarehouseConfig, value: string) => {
    setConfig((prev) => ({ ...prev, [field]: value }))
    if (testStatus !== 'idle') {
      // Stale test result — clear so users re-verify after editing
      setTestStatus('idle')
    }
  }

  const runTest = () => {
    setTestStatus('testing')
    setTimeout(() => {
      setTestStatus(Math.random() > 0.25 ? 'passed' : 'failed')
    }, 1500)
  }

  return (
    <div className='wh-config-form'>
      <div className='wh-config-form__section'>
        <span className='wh-config-form__section-label'>Warehouse Type</span>
        <div className='wh-config-form__type-row'>
          {WAREHOUSE_TYPES.map((wh) => (
            <div
              key={wh.type}
              className={`wh-config-form__type-card ${
                !wh.available ? 'wh-config-form__type-card--disabled' : ''
              }`}
            >
              <SelectableCard
                icon={wh.type === 'snowflake' ? 'flash' : 'layers'}
                title={wh.label}
                description={wh.description}
                selected={selectedType === wh.type}
                onClick={() => {
                  if (wh.available) setSelectedType(wh.type)
                }}
              />
              {!wh.available && (
                <span className='wh-config-form__coming-soon'>Coming Soon</span>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className='wh-config-form__card'>
        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>Account URL</label>
          <Input
            value={config.accountUrl}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              updateField('accountUrl', e.target.value)
            }
            placeholder='https://myorg.snowflakecomputing.com'
          />
        </div>

        <div className='wh-config-form__row'>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Database</label>
            <Input
              value={config.database}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateField('database', e.target.value)
              }
              placeholder='FLAGSMITH_PROD'
            />
          </div>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Schema</label>
            <Input
              value={config.schema}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateField('schema', e.target.value)
              }
              placeholder='PUBLIC'
            />
          </div>
        </div>

        <div className='wh-config-form__row'>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Warehouse</label>
            <Input
              value={config.warehouse}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateField('warehouse', e.target.value)
              }
              placeholder='COMPUTE_WH'
            />
          </div>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>User</label>
            <Input
              value={config.user}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateField('user', e.target.value)
              }
              placeholder='FLAGSMITH_SVC'
            />
          </div>
        </div>

        <div className='wh-config-form__divider' />

        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>Authentication Method</label>
          <div className='wh-config-form__select-display'>
            <span>{config.authMethod}</span>
            <Icon name='chevron-down' width={16} />
          </div>
        </div>

        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>Private Key</label>
          <textarea
            className='wh-config-form__textarea'
            value={config.privateKey}
            onChange={(e) => updateField('privateKey', e.target.value)}
            rows={3}
          />
        </div>

        {testStatus !== 'idle' && (
          <div
            className={`wh-config-form__test-result wh-config-form__test-result--${testStatus}`}
          >
            {testStatus === 'testing' && (
              <>
                <Icon name='refresh' width={16} />
                <span>Testing connection…</span>
              </>
            )}
            {testStatus === 'passed' && (
              <>
                <Icon name='checkmark-circle' width={16} />
                <span>
                  Connection test passed. Click <strong>Connect</strong> to save
                  and start streaming.
                </span>
              </>
            )}
            {testStatus === 'failed' && (
              <>
                <Icon name='warning' width={16} />
                <span>
                  Connection test failed. Check your credentials and try again.
                </span>
              </>
            )}
          </div>
        )}

        <div className='wh-config-form__actions'>
          <Button theme='outline' size='small' onClick={onCancel}>
            Cancel
          </Button>
          <Button
            theme='outline'
            size='small'
            onClick={runTest}
            disabled={testStatus === 'testing'}
          >
            Test Connection
          </Button>
          <Button
            theme='primary'
            size='small'
            onClick={() => onConnect(config)}
            disabled={testStatus === 'testing'}
          >
            Connect
          </Button>
        </div>
      </div>
    </div>
  )
}

ConfigForm.displayName = 'WarehouseConfigForm'
export default ConfigForm
