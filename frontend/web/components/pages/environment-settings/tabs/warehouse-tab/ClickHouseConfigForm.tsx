import React, { FC, useState } from 'react'
import Switch from 'components/Switch'
import WarehouseSetupSqlHelp from './WarehouseSetupSqlHelp'
import WarehouseConfigField from './WarehouseConfigField'
import WarehouseFormActions from './WarehouseFormActions'
import useWarehouseConnectionTest from './useWarehouseConnectionTest'
import useWarehouseFormSubmit from './useWarehouseFormSubmit'
import {
  CLICKHOUSE_SETUP_SQL_LABEL,
  getClickHouseSetupSql,
} from './clickhouseSetupSql'
import { ClickHouseConfig } from 'common/types/responses'
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
import './ConfigForm.scss'

type ClickHouseConfigFormProps = {
  environmentId: string
  onSave: (data: ClickHouseFormData) => Promise<unknown>
  onCancel?: () => void
  isEdit?: boolean
  initialConfig?: ClickHouseConfig
  initialName?: string
}

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
  const [secure] = useState(defaults.secure)
  const {
    hasTestResult,
    isTesting,
    runTest,
    showSetupSql,
    testDetail,
    testState,
    withTestReset,
  } = useWarehouseConnectionTest(environmentId, 'clickhouse')
  const { clearSaveFailed, isSaving, saveFailed, submit } =
    useWarehouseFormSubmit(onSave)

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
  const canSave = isValid && (!requiresTest || hasTestResult)

  const handleTest = () => {
    if (!canTest || isTesting) return
    clearSaveFailed()
    const { config, credentials } = buildClickHousePayload(form)
    runTest({ config, credentials })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSave) return
    submit(buildClickHousePayload(form))
  }

  return (
    <form onSubmit={handleSubmit} className='wh-config-form'>
      <div className='wh-config-form__card'>
        <WarehouseConfigField
          id='warehouse-config-host'
          label='Host'
          value={host}
          onChange={withTestReset(setHost)}
          placeholder='your-instance.clickhouse.cloud'
          disabled={isEdit}
          hint={
            isEdit
              ? "Host can't be changed. To use a different ClickHouse instance, disconnect and create a new connection."
              : 'The hostname of your ClickHouse instance, without protocol or port.'
          }
        />

        <WarehouseConfigField
          id='warehouse-config-name'
          label='Name this warehouse'
          value={name}
          onChange={setName}
          placeholder='e.g. Production ClickHouse'
        />

        <div className='wh-config-form__row'>
          <WarehouseConfigField
            id='warehouse-config-port'
            label='HTTPS port'
            value={port}
            onChange={withTestReset(setPort)}
            placeholder='8443'
            error={
              hasInvalidPort && 'Port must be a number between 1 and 65535.'
            }
          />
          <WarehouseConfigField
            id='warehouse-config-database'
            label='Database Name'
            value={database}
            onChange={withTestReset(setDatabase)}
            placeholder='flagsmith_exp'
          />
        </div>

        <WarehouseConfigField
          id='warehouse-config-username'
          label='Username'
          value={username}
          onChange={withTestReset(setUsername)}
          placeholder='The user from the setup script'
        />

        <WarehouseConfigField
          id='warehouse-config-password'
          label='Password'
          value={password}
          onChange={withTestReset(setPassword)}
          type='password'
          autoComplete='new-password'
          placeholder={isEdit ? '••••••••' : 'Password'}
          hint={
            isEdit &&
            (requiresTest && !password
              ? 'Enter your password to test the connection before saving.'
              : 'Leave blank to keep the current password.')
          }
        />

        <div className='wh-config-form__field'>
          <div className='d-flex flex-row align-items-center gap-2'>
            <Switch checked={secure} disabled />
            <label className='wh-config-form__label fs-caption text-secondary mb-0'>
              Secure connection (TLS)
            </label>
          </div>
        </div>

        {isEdit && (
          <WarehouseSetupSqlHelp
            label={CLICKHOUSE_SETUP_SQL_LABEL}
            sql={getClickHouseSetupSql(
              database.trim() || CLICKHOUSE_DEFAULTS.database,
            )}
            showInitially={showSetupSql}
          />
        )}

        <WarehouseFormActions
          isEdit={isEdit}
          onCancel={onCancel}
          onTest={handleTest}
          canTest={requiresTest && canTest}
          canSave={canSave}
          isTesting={isTesting}
          isSaving={isSaving}
          saveFailed={saveFailed}
          testState={testState}
          testDetail={testDetail}
        />
      </div>
    </form>
  )
}

ClickHouseConfigForm.displayName = 'ClickHouseConfigForm'
export default ClickHouseConfigForm
