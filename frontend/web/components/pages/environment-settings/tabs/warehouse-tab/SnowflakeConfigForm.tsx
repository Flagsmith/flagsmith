import React, { FC, useState } from 'react'
import WarehouseSetupSqlHelp from './WarehouseSetupSqlHelp'
import WarehouseConfigField from './WarehouseConfigField'
import WarehouseFormActions from './WarehouseFormActions'
import useWarehouseConnectionTest from './useWarehouseConnectionTest'
import useWarehouseFormSubmit from './useWarehouseFormSubmit'
import { invalidIf } from './warehouseFormUtils'
import { SnowflakeConfig } from 'common/types/responses'
import {
  buildSnowflakePayload,
  canTestSnowflakeConnection,
  getPrivateKeyError,
  hasSnowflakeCredentials,
  isAccountLocator,
  isSnowflakeConfigDirty,
  isSnowflakeFormValid,
  isValidAccountIdentifier,
  isValidIdentifier,
  isValidPrivateKey,
  SNOWFLAKE_DEFAULTS,
  SnowflakeFormData,
  SnowflakeFormState,
} from './snowflakeConfig'
import {
  getSnowflakeSetupSql,
  SNOWFLAKE_SETUP_SQL_LABEL,
} from './snowflakeSetupSql'
import './ConfigForm.scss'

type SnowflakeConfigFormProps = {
  environmentId: string
  onSave: (data: SnowflakeFormData) => Promise<unknown>
  onCancel?: () => void
  isEdit?: boolean
  initialConfig?: SnowflakeConfig
  initialName?: string
}

const IDENTIFIER_ERROR =
  'Use letters, numbers, underscores and $, starting with a letter or underscore.'

const SnowflakeConfigForm: FC<SnowflakeConfigFormProps> = ({
  environmentId,
  initialConfig,
  initialName = '',
  isEdit = false,
  onCancel,
  onSave,
}) => {
  const defaults = { ...SNOWFLAKE_DEFAULTS, ...initialConfig }
  const [name, setName] = useState(initialName)
  const [accountIdentifier, setAccountIdentifier] = useState(
    defaults.account_identifier,
  )
  const [warehouse, setWarehouse] = useState(defaults.warehouse)
  const [database, setDatabase] = useState(defaults.database)
  const [schema, setSchema] = useState(defaults.schema)
  const [role, setRole] = useState(defaults.role)
  const [user, setUser] = useState(defaults.user)
  const [privateKey, setPrivateKey] = useState('')
  const {
    hasTestResult,
    isTesting,
    runTest,
    showSetupSql,
    testDetail,
    testState,
    withTestReset,
  } = useWarehouseConnectionTest(environmentId, 'snowflake')
  const { clearSaveFailed, isSaving, saveErrorDetail, saveFailed, submit } =
    useWarehouseFormSubmit(onSave)

  const form: SnowflakeFormState = {
    account_identifier: accountIdentifier,
    database,
    name,
    private_key: privateKey,
    role,
    schema,
    user,
    warehouse,
  }
  const isValid = isSnowflakeFormValid(form, isEdit)
  const requiresTest = !isEdit || isSnowflakeConfigDirty(form, initialConfig)
  const canTest = canTestSnowflakeConnection(form)
  const canSave = isValid && (!requiresTest || hasTestResult)

  const handleTest = () => {
    if (!canTest || isTesting) return
    clearSaveFailed()
    runTest(buildSnowflakePayload(form))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSave) return
    submit(buildSnowflakePayload(form))
  }

  return (
    <form onSubmit={handleSubmit} className='wh-config-form'>
      <div className='wh-config-form__card'>
        <WarehouseConfigField
          id='warehouse-config-account-identifier'
          label='Account identifier'
          value={accountIdentifier}
          onChange={withTestReset(setAccountIdentifier)}
          placeholder='ORGNAME-ACCOUNTNAME'
          disabled={isEdit}
          error={
            !isEdit &&
            invalidIf(
              accountIdentifier,
              isValidAccountIdentifier(accountIdentifier),
              isAccountLocator(accountIdentifier)
                ? 'This is a legacy account locator. Use your ORGNAME-ACCOUNTNAME account identifier instead.'
                : 'Enter your account identifier as ORGNAME-ACCOUNTNAME.',
            )
          }
          hint={
            isEdit
              ? "Account identifier can't be changed. To use a different Snowflake account, disconnect and create a new connection."
              : 'From Account details in Snowflake. Pasting the account URL is fine.'
          }
        />

        <WarehouseConfigField
          id='warehouse-config-name'
          label='Name this warehouse'
          value={name}
          onChange={setName}
          placeholder='e.g. Production Snowflake'
        />

        <WarehouseConfigField
          id='warehouse-config-warehouse'
          label='Warehouse'
          value={warehouse}
          onChange={withTestReset(setWarehouse)}
          placeholder='FLAGSMITH_WH'
          error={invalidIf(
            warehouse,
            isValidIdentifier(warehouse),
            IDENTIFIER_ERROR,
          )}
        />

        <div className='wh-config-form__row'>
          <WarehouseConfigField
            id='warehouse-config-database'
            label='Database'
            value={database}
            onChange={withTestReset(setDatabase)}
            placeholder='FLAGSMITH'
            error={invalidIf(
              database,
              isValidIdentifier(database),
              IDENTIFIER_ERROR,
            )}
          />
          <WarehouseConfigField
            id='warehouse-config-schema'
            label='Schema'
            value={schema}
            onChange={withTestReset(setSchema)}
            placeholder='FLAGSMITH_EXP'
            error={invalidIf(
              schema,
              isValidIdentifier(schema),
              IDENTIFIER_ERROR,
            )}
          />
        </div>

        <div className='wh-config-form__row'>
          <WarehouseConfigField
            id='warehouse-config-role'
            label='Role'
            value={role}
            onChange={withTestReset(setRole)}
            placeholder='FLAGSMITH_ROLE'
            error={invalidIf(role, isValidIdentifier(role), IDENTIFIER_ERROR)}
            hint="Must be the user's default role."
          />
          <WarehouseConfigField
            id='warehouse-config-user'
            label='User'
            value={user}
            onChange={withTestReset(setUser)}
            autoComplete='off'
            placeholder='FLAGSMITH_SERVICE'
            error={invalidIf(user, isValidIdentifier(user), IDENTIFIER_ERROR)}
          />
        </div>

        <WarehouseConfigField
          id='warehouse-config-private-key'
          label='Private key'
          value={privateKey}
          onChange={withTestReset(setPrivateKey)}
          textarea
          autoComplete='off'
          placeholder={isEdit ? '••••••••' : '-----BEGIN PRIVATE KEY-----'}
          error={invalidIf(
            privateKey,
            isValidPrivateKey(privateKey),
            getPrivateKeyError(privateKey) ?? '',
          )}
          hint={
            isEdit &&
            (requiresTest && !hasSnowflakeCredentials(form)
              ? 'Paste the private key to test the connection before saving.'
              : 'Leave blank to keep the current key.')
          }
        />

        {isEdit && (
          <WarehouseSetupSqlHelp
            label={SNOWFLAKE_SETUP_SQL_LABEL}
            sql={getSnowflakeSetupSql({
              database,
              role,
              schema,
              user,
              warehouse,
            })}
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

SnowflakeConfigForm.displayName = 'SnowflakeConfigForm'
export default SnowflakeConfigForm
