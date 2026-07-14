import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import Switch from 'components/Switch'
import ErrorMessage from 'components/ErrorMessage'
import { ClickHouseConfig } from 'common/types/responses'
import {
  buildClickHousePayload,
  CLICKHOUSE_DEFAULTS,
  ClickHouseFormData,
  ClickHouseFormState,
  isClickHouseFormValid,
} from './clickhouseConfig'
import './ConfigForm.scss'

type ClickHouseConfigFormProps = {
  onSave: (data: ClickHouseFormData) => Promise<unknown>
  onCancel: () => void
  isEdit?: boolean
  initialConfig?: ClickHouseConfig
  initialName?: string
}

const getButtonLabel = (isEdit: boolean, isSaving: boolean): string => {
  if (isSaving) return isEdit ? 'Saving...' : 'Creating...'
  return isEdit ? 'Save changes' : 'Save and continue'
}

const ClickHouseConfigForm: FC<ClickHouseConfigFormProps> = ({
  initialConfig,
  initialName = '',
  isEdit = false,
  onCancel,
  onSave,
}) => {
  const defaults = { ...CLICKHOUSE_DEFAULTS, ...initialConfig }
  const [name, setName] = useState(initialName)
  const [host, setHost] = useState(defaults.host)
  const [port, setPort] = useState(String(defaults.port))
  const [database, setDatabase] = useState(defaults.database)
  const [username, setUsername] = useState(defaults.username)
  const [password, setPassword] = useState('')
  const [secure, setSecure] = useState(defaults.secure)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState(false)

  const form: ClickHouseFormState = {
    database,
    host,
    name,
    password,
    port,
    secure,
    username,
  }
  const isValid = isClickHouseFormValid(form, isEdit)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValid) return

    setIsSaving(true)
    setError(false)
    try {
      await onSave(buildClickHousePayload(form))
    } catch {
      setError(true)
      setIsSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className='wh-config-form'>
      <div className='wh-config-form__card'>
        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>Host</label>
          <Input
            value={host}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setHost(e.target.value)
            }
            placeholder='your-instance.clickhouse.cloud'
            disabled={isEdit}
          />
          <span className='wh-config-form__hint'>
            {isEdit
              ? "Host can't be changed. To use a different ClickHouse instance, disconnect and create a new connection."
              : 'The hostname of your ClickHouse instance, without protocol or port.'}
          </span>
        </div>

        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>Name</label>
          <Input
            value={name}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setName(e.target.value)
            }
            placeholder='e.g. Production ClickHouse'
          />
        </div>

        <div className='wh-config-form__row'>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Port</label>
            <Input
              value={port}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setPort(e.target.value)
              }
              placeholder='9440'
            />
          </div>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Database</label>
            <Input
              value={database}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setDatabase(e.target.value)
              }
              placeholder='flagsmith'
            />
          </div>
        </div>

        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>Username</label>
          <Input
            value={username}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setUsername(e.target.value)
            }
            placeholder='default'
          />
        </div>

        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>Password</label>
          <Input
            value={password}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setPassword(e.target.value)
            }
            type='password'
            placeholder={isEdit ? '••••••••' : 'Password'}
          />
          {isEdit && (
            <span className='wh-config-form__hint'>
              Leave blank to keep the current password.
            </span>
          )}
        </div>

        <div className='wh-config-form__field'>
          <div className='d-flex flex-row align-items-center gap-2'>
            <Switch checked={secure} onChange={setSecure} />
            <label className='wh-config-form__label mb-0'>
              Secure connection (TLS)
            </label>
          </div>
        </div>

        {error && (
          <ErrorMessage
            error={`Failed to ${
              isEdit ? 'update' : 'create'
            } warehouse connection. Please try again.`}
          />
        )}

        <div className='wh-config-form__actions'>
          <Button theme='outline' size='small' onClick={onCancel} type='button'>
            Cancel
          </Button>
          <Button
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

ClickHouseConfigForm.displayName = 'ClickHouseConfigForm'
export default ClickHouseConfigForm
