import React, { FC, useState } from 'react'
import Utils from 'common/utils/utils'
import { PostgresConfig } from 'common/types/responses'
import WarehouseSetupSqlHelp from './WarehouseSetupSqlHelp'
import WarehouseConfigField from './WarehouseConfigField'
import WarehouseFormActions from './WarehouseFormActions'
import WarehouseTlsSwitch from './WarehouseTlsSwitch'
import useWarehouseConnectionTest from './useWarehouseConnectionTest'
import useWarehouseFormSubmit from './useWarehouseFormSubmit'
import { isValidPort } from './clickhouseConfig'
import { invalidIf } from './warehouseFormUtils'
import {
  buildPostgresPayload,
  canTestPostgresConnection,
  isPostgresConfigDirty,
  isPostgresFormValid,
  isValidPostgresHost,
  isValidPostgresSchema,
  POSTGRES_DEFAULTS,
  PostgresFormData,
  PostgresFormState,
} from './postgresConfig'
import {
  getPostgresSetupSql,
  POSTGRES_SETUP_SQL_LABEL,
} from './postgresSetupSql'
import './ConfigForm.scss'

type PostgresConfigFormProps = {
  environmentId: string
  onSave: (data: PostgresFormData) => Promise<unknown>
  onCancel?: () => void
  isEdit?: boolean
  initialConfig?: PostgresConfig
  initialName?: string
}

const PostgresConfigForm: FC<PostgresConfigFormProps> = ({
  environmentId,
  initialConfig,
  initialName = '',
  isEdit = false,
  onCancel,
  onSave,
}) => {
  const isSaas = !!Utils.isSaas()
  const defaults = { ...POSTGRES_DEFAULTS, ...initialConfig }
  const [name, setName] = useState(initialName)
  const [host, setHost] = useState(defaults.host)
  const [port, setPort] = useState(String(defaults.port))
  const [database, setDatabase] = useState(defaults.database)
  const [schema, setSchema] = useState(defaults.schema)
  const [username, setUsername] = useState(defaults.username)
  const [password, setPassword] = useState('')
  const [sslmode, setSslmode] = useState(defaults.sslmode)
  const {
    hasTestResult,
    isTesting,
    runTest,
    showSetupSql,
    testDetail,
    testState,
    withTestReset,
  } = useWarehouseConnectionTest(environmentId, 'postgres')
  const { clearSaveFailed, isSaving, saveErrorDetail, saveFailed, submit } =
    useWarehouseFormSubmit(onSave)

  const form: PostgresFormState = {
    database,
    host,
    name,
    password,
    port,
    schema,
    sslmode,
    username,
  }
  const isValid = isPostgresFormValid(form, isEdit)
  const requiresTest = !isEdit || isPostgresConfigDirty(form, initialConfig)
  const canTest = canTestPostgresConnection(form, isEdit)
  const canSave = isValid && (!requiresTest || hasTestResult)

  const handleTest = () => {
    if (!canTest || isTesting) return
    clearSaveFailed()
    runTest(buildPostgresPayload(form))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSave) return
    submit(buildPostgresPayload(form))
  }

  return (
    <form onSubmit={handleSubmit} className='wh-config-form'>
      <div className='wh-config-form__card'>
        <WarehouseConfigField
          id='warehouse-config-host'
          label='Host'
          value={host}
          onChange={withTestReset(setHost)}
          placeholder='db.example.com'
          disabled={isEdit}
          error={
            !isEdit &&
            invalidIf(
              host,
              isValidPostgresHost(host),
              'Enter a hostname or IP address, without a scheme or port.',
            )
          }
          hint={
            isEdit &&
            "Host can't be changed. To use a different PostgreSQL database, disconnect and create a new connection."
          }
        />

        <WarehouseConfigField
          id='warehouse-config-name'
          label='Name this warehouse'
          value={name}
          onChange={setName}
          placeholder='e.g. Production PostgreSQL'
        />

        <div className='wh-config-form__row'>
          <WarehouseConfigField
            id='warehouse-config-port'
            label='Port'
            value={port}
            onChange={withTestReset(setPort)}
            placeholder='5432'
            error={invalidIf(
              port,
              isValidPort(port),
              'Port must be a number between 1 and 65535.',
            )}
          />
          <WarehouseConfigField
            id='warehouse-config-database'
            label='Database'
            value={database}
            onChange={withTestReset(setDatabase)}
            placeholder='postgres'
          />
        </div>

        <WarehouseConfigField
          id='warehouse-config-schema'
          label='Schema'
          value={schema}
          onChange={withTestReset(setSchema)}
          placeholder='flagsmith_exp'
          error={invalidIf(
            schema,
            isValidPostgresSchema(schema),
            'Use lowercase letters, numbers and underscores, not starting with a number.',
          )}
        />

        <WarehouseConfigField
          id='warehouse-config-username'
          label='Username'
          value={username}
          onChange={withTestReset(setUsername)}
          autoComplete='off'
          placeholder='The user you created in step 1'
          hint='Usernames are lowercase unless they were quoted when the user was created.'
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

        <WarehouseTlsSwitch
          checked={sslmode === 'require'}
          disabled={isSaas}
          onChange={(checked) =>
            withTestReset(setSslmode)(checked ? 'require' : 'disable')
          }
        />

        {isEdit && (
          <WarehouseSetupSqlHelp
            label={POSTGRES_SETUP_SQL_LABEL}
            sql={getPostgresSetupSql(schema.trim() || POSTGRES_DEFAULTS.schema)}
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
          saveErrorDetail={saveErrorDetail}
          saveFailed={saveFailed}
          testState={testState}
          testDetail={testDetail}
        />
      </div>
    </form>
  )
}

PostgresConfigForm.displayName = 'PostgresConfigForm'
export default PostgresConfigForm
