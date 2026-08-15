import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import ErrorMessage from 'components/ErrorMessage'
import { SnowflakeConfig } from 'common/types/responses'
import { getButtonLabel } from './warehouseFormUtils'
import './ConfigForm.scss'

export type ConfigFormData = SnowflakeConfig & { name: string }

type ConfigFormProps = {
  onSave: (data: ConfigFormData) => Promise<unknown>
  onCancel: () => void
  isEdit?: boolean
  initialConfig?: SnowflakeConfig
  initialName?: string
}

const DEFAULTS: SnowflakeConfig = {
  account_identifier: '',
  database: 'FLAGSMITH',
  role: 'FLAGSMITH_LOADER',
  schema: 'ANALYTICS',
  user: 'FLAGSMITH_SERVICE',
  warehouse: 'COMPUTE_WH',
}

const ConfigForm: FC<ConfigFormProps> = ({
  initialConfig,
  initialName = '',
  isEdit = false,
  onCancel,
  onSave,
}) => {
  const defaults = { ...DEFAULTS, ...initialConfig }
  const [name, setName] = useState(initialName)
  const [accountIdentifier, setAccountIdentifier] = useState(
    defaults.account_identifier,
  )
  const [warehouse, setWarehouse] = useState(defaults.warehouse)
  const [database, setDatabase] = useState(defaults.database)
  const [schema, setSchema] = useState(defaults.schema)
  const [role, setRole] = useState(defaults.role)
  const [user, setUser] = useState(defaults.user)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState(false)

  const isValid =
    !!name &&
    !!accountIdentifier &&
    !!warehouse &&
    !!database &&
    !!schema &&
    !!role &&
    !!user

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValid) return

    setIsSaving(true)
    setError(false)
    try {
      await onSave({
        account_identifier: accountIdentifier,
        database,
        name,
        role,
        schema,
        user,
        warehouse,
      })
    } catch {
      setError(true)
      setIsSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className='wh-config-form'>
      <div className='wh-config-form__card'>
        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>Account Identifier</label>
          <Input
            value={accountIdentifier}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setAccountIdentifier(e.target.value)
            }
            placeholder='xy12345.us-east-1'
            disabled={isEdit}
          />
          <span className='wh-config-form__hint'>
            {isEdit
              ? "Identifier can't be changed. To use a different Snowflake account, disconnect and create a new connection."
              : 'The Snowflake account identifier — the part of your Snowflake URL before .snowflakecomputing.com.'}
          </span>
        </div>

        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>Name</label>
          <Input
            value={name}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setName(e.target.value)
            }
            placeholder='e.g. Production Snowflake'
          />
        </div>

        <div className='wh-config-form__row'>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Warehouse</label>
            <Input
              value={warehouse}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setWarehouse(e.target.value)
              }
              placeholder='COMPUTE_WH'
            />
          </div>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Database</label>
            <Input
              value={database}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setDatabase(e.target.value)
              }
              placeholder='FLAGSMITH'
            />
          </div>
        </div>

        <div className='wh-config-form__row'>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Schema</label>
            <Input
              value={schema}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setSchema(e.target.value)
              }
              placeholder='ANALYTICS'
            />
          </div>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Role</label>
            <Input
              value={role}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setRole(e.target.value)
              }
              placeholder='FLAGSMITH_LOADER'
            />
          </div>
        </div>

        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>User</label>
          <Input
            value={user}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setUser(e.target.value)
            }
            placeholder='FLAGSMITH_SERVICE'
          />
        </div>

        {!isEdit && (
          <div className='wh-config-form__note'>
            Flagsmith generates an RSA key pair on save &mdash; no passwords or
            private keys to type. You&apos;ll get a setup script to run in
            Snowflake after saving.
          </div>
        )}

        {error && (
          <ErrorMessage
            error={`Failed to ${
              isEdit ? 'update' : 'create'
            } warehouse connection. Please try again.`}
          />
        )}

        <div className='wh-config-form__actions'>
          <Button
            id='warehouse-config-cancel'
            theme='outline'
            size='small'
            onClick={onCancel}
            type='button'
          >
            Cancel
          </Button>
          <Button
            id='warehouse-config-save'
            theme='primary'
            size='small'
            type='submit'
            disabled={isSaving || !isValid}
          >
            {getButtonLabel(isEdit, isSaving)}
          </Button>
        </div>
      </div>
    </form>
  )
}

ConfigForm.displayName = 'WarehouseConfigForm'
export default ConfigForm
