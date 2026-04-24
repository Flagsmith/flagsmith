import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import SelectableCard from 'components/experiments-v2/shared/SelectableCard'
import {
  MOCK_CONFIG,
  WAREHOUSE_TYPES,
  WarehouseConfig,
  WarehouseType,
} from 'components/warehouse/types'
import './ConfigForm.scss'

type ConfigFormProps = {
  /** Commits the config and transitions to the pending-setup state. */
  onConnect: (config: WarehouseConfig) => void
  onCancel: () => void
  /**
   * Editing an existing connection. `type` and `accountIdentifier` become
   * read-only — per the API they're immutable (PATCH rejects changes).
   * Changing either means disconnecting and starting over.
   */
  isEdit?: boolean
  /** Prefilled config when editing. Ignored when `isEdit` is false. */
  initialConfig?: WarehouseConfig
}

const ConfigForm: FC<ConfigFormProps> = ({
  initialConfig,
  isEdit = false,
  onCancel,
  onConnect,
}) => {
  const [config, setConfig] = useState<WarehouseConfig>(
    initialConfig ?? MOCK_CONFIG,
  )
  const [selectedType, setSelectedType] = useState<WarehouseType>(config.type)

  const updateField = (field: keyof WarehouseConfig, value: string) => {
    setConfig((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <div className='wh-config-form'>
      <div className='wh-config-form__section'>
        <span className='wh-config-form__section-label'>Warehouse Type</span>
        <div className='wh-config-form__type-row'>
          {WAREHOUSE_TYPES.map((wh) => {
            const locked = isEdit && wh.type !== selectedType
            const cardDisabled = !wh.available || isEdit
            return (
              <div
                key={wh.type}
                className={`wh-config-form__type-card ${
                  cardDisabled ? 'wh-config-form__type-card--disabled' : ''
                }`}
              >
                <SelectableCard
                  icon={wh.type === 'snowflake' ? 'flash' : 'layers'}
                  title={wh.label}
                  description={wh.description}
                  selected={selectedType === wh.type}
                  onClick={() => {
                    if (wh.available && !isEdit) setSelectedType(wh.type)
                  }}
                />
                {!wh.available && !locked && (
                  <span className='wh-config-form__coming-soon'>
                    Coming Soon
                  </span>
                )}
              </div>
            )
          })}
        </div>
        {isEdit && (
          <span className='wh-config-form__hint'>
            Warehouse type can&apos;t be changed. To move to a different
            provider, disconnect and create a new connection.
          </span>
        )}
      </div>

      <div className='wh-config-form__card'>
        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>Account Identifier</label>
          <Input
            value={config.accountIdentifier}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              updateField('accountIdentifier', e.target.value)
            }
            placeholder='xy12345.us-east-1'
            disabled={isEdit}
          />
          <span className='wh-config-form__hint'>
            {isEdit
              ? "Identifier can't be changed. To move to a different Snowflake account, disconnect and re-connect."
              : 'The Snowflake account identifier — the part of your Snowflake URL before .snowflakecomputing.com.'}
          </span>
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
            <label className='wh-config-form__label'>Database</label>
            <Input
              value={config.database}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateField('database', e.target.value)
              }
              placeholder='FLAGSMITH'
            />
          </div>
        </div>

        <div className='wh-config-form__row'>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Schema</label>
            <Input
              value={config.schema}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateField('schema', e.target.value)
              }
              placeholder='ANALYTICS'
            />
          </div>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Role</label>
            <Input
              value={config.role}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateField('role', e.target.value)
              }
              placeholder='FLAGSMITH_LOADER'
            />
          </div>
        </div>

        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>User</label>
          <Input
            value={config.user}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              updateField('user', e.target.value)
            }
            placeholder='FLAGSMITH_SERVICE'
          />
        </div>

        {!isEdit && (
          <div className='wh-config-form__note'>
            Flagsmith generates an RSA key pair on save — no passwords or
            private keys to type. You&apos;ll get a setup script to run in
            Snowflake after saving.
          </div>
        )}

        <div className='wh-config-form__actions'>
          <Button theme='outline' size='small' onClick={onCancel}>
            Cancel
          </Button>
          <Button
            theme='primary'
            size='small'
            onClick={() => onConnect(config)}
          >
            {isEdit ? 'Save changes' : 'Save and continue'}
          </Button>
        </div>
      </div>
    </div>
  )
}

ConfigForm.displayName = 'WarehouseConfigForm'
export default ConfigForm
