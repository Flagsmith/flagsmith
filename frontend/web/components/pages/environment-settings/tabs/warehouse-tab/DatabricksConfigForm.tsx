import React, { FC, useState } from 'react'
import WarehouseSetupSqlHelp from './WarehouseSetupSqlHelp'
import WarehouseConfigField from './WarehouseConfigField'
import WarehouseFormActions from './WarehouseFormActions'
import useWarehouseConnectionTest from './useWarehouseConnectionTest'
import useWarehouseFormSubmit from './useWarehouseFormSubmit'
import { DatabricksConfig } from 'common/types/responses'
import {
  buildDatabricksPayload,
  canTestDatabricksConnection,
  DATABRICKS_DEFAULTS,
  DatabricksFormData,
  DatabricksFormState,
  getWorkspaceIdFromUrl,
  hasDatabricksCredentials,
  isDatabricksConfigDirty,
  isDatabricksFormValid,
  isValidDatabricksHost,
  isValidIdentifier,
  isValidRegion,
  isValidWarehouseId,
  isValidWorkspaceId,
} from './databricksConfig'
import {
  DATABRICKS_SETUP_SQL_LABEL,
  getDatabricksSetupSql,
} from './databricksSetupSql'
import './ConfigForm.scss'

type DatabricksConfigFormProps = {
  environmentId: string
  onSave: (data: DatabricksFormData) => Promise<unknown>
  onCancel?: () => void
  isEdit?: boolean
  initialConfig?: DatabricksConfig
  initialName?: string
}

const IDENTIFIER_ERROR = 'Use letters, numbers and underscores only.'

const invalidIf = (value: string, isValid: boolean, message: string) =>
  !!value.trim() && !isValid && message

const DatabricksConfigForm: FC<DatabricksConfigFormProps> = ({
  environmentId,
  initialConfig,
  initialName = '',
  isEdit = false,
  onCancel,
  onSave,
}) => {
  const defaults = { ...DATABRICKS_DEFAULTS, ...initialConfig }
  const [name, setName] = useState(initialName)
  const [host, setHost] = useState(defaults.host)
  const [workspaceId, setWorkspaceId] = useState(defaults.workspace_id)
  const [region, setRegion] = useState(defaults.region)
  const [warehouseId, setWarehouseId] = useState(defaults.warehouse_id)
  const [catalog, setCatalog] = useState(defaults.catalog)
  const [schema, setSchema] = useState(defaults.schema)
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const {
    hasTestResult,
    isTesting,
    runTest,
    showSetupSql,
    testDetail,
    testState,
    withTestReset,
  } = useWarehouseConnectionTest(environmentId, 'databricks')
  const { clearSaveFailed, isSaving, saveFailed, submit } =
    useWarehouseFormSubmit(onSave)

  const form: DatabricksFormState = {
    catalog,
    client_id: clientId,
    client_secret: clientSecret,
    host,
    name,
    region,
    schema,
    warehouse_id: warehouseId,
    workspace_id: workspaceId,
  }
  const isValid = isDatabricksFormValid(form, isEdit)
  const requiresTest = !isEdit || isDatabricksConfigDirty(form, initialConfig)
  const canTest = canTestDatabricksConnection(form)
  const canSave = isValid && (!requiresTest || hasTestResult)

  const handleHostChange = (value: string) => {
    withTestReset(setHost)(value)
    const pastedWorkspaceId = getWorkspaceIdFromUrl(value)
    if (pastedWorkspaceId && !workspaceId.trim()) {
      setWorkspaceId(pastedWorkspaceId)
    }
  }

  const handleTest = () => {
    if (!canTest || isTesting) return
    clearSaveFailed()
    runTest(buildDatabricksPayload(form))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSave) return
    submit(buildDatabricksPayload(form))
  }

  return (
    <form onSubmit={handleSubmit} className='wh-config-form'>
      <div className='wh-config-form__card'>
        <WarehouseConfigField
          id='warehouse-config-host'
          label='Server hostname'
          value={host}
          onChange={handleHostChange}
          placeholder='dbc-1234abcd-5678.cloud.databricks.com'
          disabled={isEdit}
          error={
            !isEdit &&
            invalidIf(
              host,
              isValidDatabricksHost(host),
              'Enter a Databricks workspace hostname, e.g. dbc-1234.cloud.databricks.com.',
            )
          }
          hint={
            isEdit
              ? "Server hostname can't be changed. To use a different Databricks workspace, disconnect and create a new connection."
              : 'From Connection details on your SQL warehouse. Pasting the full URL is fine.'
          }
        />

        <div className='wh-config-form__row'>
          <WarehouseConfigField
            id='warehouse-config-workspace-id'
            label='Workspace ID'
            value={workspaceId}
            onChange={withTestReset(setWorkspaceId)}
            placeholder='1234567890123456'
            error={invalidIf(
              workspaceId,
              isValidWorkspaceId(workspaceId),
              'Enter the numeric workspace ID.',
            )}
            hint='The number after ?o= in your workspace URL.'
          />
          <WarehouseConfigField
            id='warehouse-config-region'
            label='Region'
            value={region}
            onChange={withTestReset(setRegion)}
            placeholder='us-east-1'
            error={invalidIf(
              region,
              isValidRegion(region),
              'Enter the workspace region, e.g. us-east-1.',
            )}
            hint='Shown under the workspace name in the workspace switcher, e.g. us-east-1, eastus2 or us-central1.'
          />
        </div>

        <WarehouseConfigField
          id='warehouse-config-name'
          label='Name this warehouse'
          value={name}
          onChange={setName}
          placeholder='e.g. Production Databricks'
        />

        <WarehouseConfigField
          id='warehouse-config-warehouse-id'
          label='Warehouse ID'
          value={warehouseId}
          onChange={withTestReset(setWarehouseId)}
          placeholder='1234567890abcdef'
          error={invalidIf(
            warehouseId,
            isValidWarehouseId(warehouseId),
            "Use the ID from the warehouse's HTTP path, e.g. 1234567890abcdef.",
          )}
          hint='The last part of the HTTP path. Pasting the full HTTP path is fine.'
        />

        <div className='wh-config-form__row'>
          <WarehouseConfigField
            id='warehouse-config-catalog'
            label='Catalog'
            value={catalog}
            onChange={withTestReset(setCatalog)}
            placeholder='workspace'
            error={invalidIf(
              catalog,
              isValidIdentifier(catalog),
              IDENTIFIER_ERROR,
            )}
          />
          <WarehouseConfigField
            id='warehouse-config-schema'
            label='Schema'
            value={schema}
            onChange={withTestReset(setSchema)}
            placeholder='flagsmith_exp'
            error={invalidIf(
              schema,
              isValidIdentifier(schema),
              IDENTIFIER_ERROR,
            )}
          />
        </div>

        <WarehouseConfigField
          id='warehouse-config-client-id'
          label='Client ID'
          value={clientId}
          onChange={withTestReset(setClientId)}
          autoComplete='off'
          placeholder="The service principal's client ID"
        />

        <WarehouseConfigField
          id='warehouse-config-client-secret'
          label='Client secret'
          value={clientSecret}
          onChange={withTestReset(setClientSecret)}
          type='password'
          autoComplete='new-password'
          placeholder={isEdit ? '••••••••' : 'Client secret'}
          hint={
            isEdit &&
            (requiresTest && !hasDatabricksCredentials(form)
              ? 'Enter the client ID and secret to test the connection before saving.'
              : 'Leave blank to keep the current credentials.')
          }
        />

        {isEdit && (
          <WarehouseSetupSqlHelp
            label={DATABRICKS_SETUP_SQL_LABEL}
            sql={getDatabricksSetupSql({ catalog, clientId, schema })}
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

DatabricksConfigForm.displayName = 'DatabricksConfigForm'
export default DatabricksConfigForm
