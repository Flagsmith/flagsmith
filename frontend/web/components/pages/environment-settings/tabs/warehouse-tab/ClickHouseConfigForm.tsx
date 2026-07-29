import React, { FC, useRef, useState } from 'react'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import Switch from 'components/Switch'
import ErrorMessage from 'components/ErrorMessage'
import FieldError from 'components/base/forms/FieldError'
import WarningMessage from 'components/WarningMessage'
import { ClickHouseConfig } from 'common/types/responses'
import { useTestWarehouseConnectionConfigMutation } from 'common/services/useWarehouseConnection'
import {
  buildClickHousePayload,
  canTestClickHouseConnection,
  CLICKHOUSE_DEFAULTS,
  ClickHouseFormData,
  ClickHouseFormState,
  isClickHouseConfigDirty,
  isClickHouseFormValid,
  isValidPort,
} from './clickhouseConfig'
import {
  getButtonLabel,
  getTestFailureWarning,
  getWarehouseErrorMessage,
} from './warehouseFormUtils'
import './ConfigForm.scss'

type ClickHouseConfigFormProps = {
  environmentId: string
  onSave: (data: ClickHouseFormData) => Promise<unknown>
  onCancel?: () => void
  isEdit?: boolean
  initialConfig?: ClickHouseConfig
  initialName?: string
}

type TestState = 'idle' | 'connected' | 'errored'

const ClickHouseConfigForm: FC<ClickHouseConfigFormProps> = ({
  environmentId,
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
  const [testState, setTestState] = useState<TestState>('idle')
  const [testDetail, setTestDetail] = useState<string | null>(null)
  const testRevision = useRef(0)

  const [testConnectionConfig, { isLoading: isTesting }] =
    useTestWarehouseConnectionConfigMutation()

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
  const requiresTest = !isEdit || isClickHouseConfigDirty(form, initialConfig)
  const canTest = canTestClickHouseConnection(form)
  const hasInvalidPort = !!port && !isValidPort(port)
  const canSave = isValid && (!requiresTest || testState !== 'idle')

  const setField =
    <T,>(setter: (value: T) => void) =>
    (value: T) => {
      setter(value)
      testRevision.current += 1
      setTestState('idle')
      setTestDetail(null)
    }

  const handleTest = async () => {
    if (!canTest || isTesting) return
    setError(false)
    const revision = testRevision.current
    try {
      const { config, credentials } = buildClickHousePayload(form)
      const result = await testConnectionConfig({
        config,
        credentials,
        environmentId,
        warehouse_type: 'clickhouse',
      }).unwrap()
      if (revision !== testRevision.current) return
      if (result.status === 'connected') {
        setTestState('connected')
        setTestDetail(null)
        toast('Connection verified')
      } else {
        setTestState('errored')
        setTestDetail(result.status_detail)
      }
    } catch {
      if (revision !== testRevision.current) return
      setTestState('errored')
      setTestDetail(null)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSave || isSaving) return

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
              setField(setHost)(e.target.value)
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
                setField(setPort)(e.target.value)
              }
              placeholder='9440'
              aria-invalid={hasInvalidPort}
              aria-describedby={
                hasInvalidPort ? 'warehouse-config-port-error' : undefined
              }
            />
            <FieldError
              id='warehouse-config-port-error'
              error={
                hasInvalidPort && 'Port must be a number between 1 and 65535.'
              }
            />
          </div>
          <div className='wh-config-form__field'>
            <label className='wh-config-form__label'>Database</label>
            <Input
              value={database}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setField(setDatabase)(e.target.value)
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
              setField(setUsername)(e.target.value)
            }
            placeholder='default'
          />
        </div>

        <div className='wh-config-form__field'>
          <label className='wh-config-form__label'>Password</label>
          <Input
            value={password}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setField(setPassword)(e.target.value)
            }
            type='password'
            autoComplete='new-password'
            placeholder={isEdit ? '••••••••' : 'Password'}
          />
          {isEdit && (
            <span className='wh-config-form__hint'>
              {requiresTest && !password
                ? 'Enter your password to test the connection before saving.'
                : 'Leave blank to keep the current password.'}
            </span>
          )}
        </div>

        <div className='wh-config-form__field'>
          <div className='d-flex flex-row align-items-center gap-2'>
            <Switch checked={secure} onChange={setField(setSecure)} />
            <label className='wh-config-form__label mb-0'>
              Secure connection (TLS)
            </label>
          </div>
        </div>

        {error && <ErrorMessage error={getWarehouseErrorMessage(isEdit)} />}

        <div className='wh-config-form__actions'>
          {isEdit && onCancel && (
            <Button
              id='warehouse-config-cancel'
              theme='outline'
              size='small'
              onClick={onCancel}
              type='button'
            >
              Cancel
            </Button>
          )}
          <Button
            id='warehouse-config-test'
            theme='outline'
            size='small'
            type='button'
            onClick={handleTest}
            disabled={!requiresTest || !canTest || isTesting}
          >
            {isTesting ? 'Testing...' : 'Test connection'}
          </Button>
          <Button
            id='warehouse-config-save'
            theme='primary'
            size='small'
            type='submit'
            disabled={isSaving || !canSave}
          >
            {getButtonLabel(isEdit, isSaving)}
          </Button>
        </div>

        {testState === 'connected' && (
          <div className='d-flex justify-content-end'>
            <span className='wh-config-form__hint text-success'>
              Connection verified. You can now save.
            </span>
          </div>
        )}
        {testState === 'errored' && (
          <div className='d-flex justify-content-end'>
            <WarningMessage
              warningMessage={getTestFailureWarning(testDetail)}
              warningMessageClass='mb-0'
            />
          </div>
        )}
      </div>
    </form>
  )
}

ClickHouseConfigForm.displayName = 'ClickHouseConfigForm'
export default ClickHouseConfigForm
