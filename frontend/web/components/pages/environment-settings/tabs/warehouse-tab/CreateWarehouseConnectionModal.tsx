import { FC, FormEvent, useMemo, useState } from 'react'
import { Req } from 'common/types/requests'
import { WarehouseConnection } from 'common/types/responses'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import SearchableSelect from 'components/base/select/SearchableSelect'

type CreateWarehouseConnectionModalProps = {
  connection?: WarehouseConnection
  save: (
    data: Omit<Req['createWarehouseConnection'], 'environmentId'>,
  ) => Promise<unknown>
}

const warehouseTypeOptions = [{ label: 'Snowflake', value: 'snowflake' }]

const getButtonLabel = (isEdit: boolean, isSaving: boolean): string => {
  if (isSaving) return isEdit ? 'Saving...' : 'Creating...'
  return isEdit ? 'Save Changes' : 'Create Connection'
}

const CreateWarehouseConnectionModal: FC<
  CreateWarehouseConnectionModalProps
> = ({ connection, save }) => {
  const isEdit = !!connection
  const initialConfig = connection?.config as Record<string, string> | null

  const [name, setName] = useState(connection?.name ?? '')
  const [warehouseType] = useState(connection?.warehouse_type ?? 'snowflake')
  const [accountIdentifier, setAccountIdentifier] = useState(
    initialConfig?.account_identifier ?? '',
  )
  const [warehouse, setWarehouse] = useState(
    initialConfig?.warehouse ?? 'COMPUTE_WH',
  )
  const [database, setDatabase] = useState(
    initialConfig?.database ?? 'FLAGSMITH',
  )
  const [schema, setSchema] = useState(initialConfig?.schema ?? 'ANALYTICS')
  const [role, setRole] = useState(initialConfig?.role ?? 'FLAGSMITH_LOADER')
  const [user, setUser] = useState(initialConfig?.user ?? 'FLAGSMITH_SERVICE')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState(false)

  const isValid = !!name && !!accountIdentifier

  const hasChanges = useMemo(() => {
    if (!isEdit) return true
    return (
      name !== (connection?.name ?? '') ||
      accountIdentifier !== (initialConfig?.account_identifier ?? '') ||
      warehouse !== (initialConfig?.warehouse ?? '') ||
      database !== (initialConfig?.database ?? '') ||
      schema !== (initialConfig?.schema ?? '') ||
      role !== (initialConfig?.role ?? '') ||
      user !== (initialConfig?.user ?? '')
    )
  }, [
    isEdit,
    connection,
    initialConfig,
    name,
    accountIdentifier,
    warehouse,
    database,
    schema,
    role,
    user,
  ])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!isValid || !hasChanges) return

    setIsSaving(true)
    setError(false)
    try {
      await save({
        config: {
          account_identifier: accountIdentifier,
          database,
          role,
          schema,
          user,
          warehouse,
        },
        name,
        warehouse_type: warehouseType,
      })
      closeModal()
      toast(
        isEdit
          ? 'Warehouse connection updated'
          : 'Warehouse connection created',
      )
    } catch {
      setError(true)
      setIsSaving(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className='px-4 py-2 d-flex flex-column gap-2'
    >
      <InputGroup
        title='Type'
        noMargin
        component={
          <SearchableSelect
            placeholder='Select type'
            options={warehouseTypeOptions}
            value={warehouseType}
            displayedLabel={
              warehouseTypeOptions.find((o) => o.value === warehouseType)?.label
            }
            isSearchable={false}
            onChange={() => {}}
          />
        }
      />
      <InputGroup
        title='Name'
        noMargin
        inputProps={{
          className: 'w-100',
          name: 'name',
        }}
        value={name}
        onChange={(e: InputEvent) => setName(Utils.safeParseEventValue(e))}
        isValid={!!name}
        placeholder='e.g. Production Snowflake'
      />
      <InputGroup
        title='Account Identifier'
        noMargin
        inputProps={{
          className: 'w-100',
          name: 'accountIdentifier',
        }}
        value={accountIdentifier}
        onChange={(e: InputEvent) =>
          setAccountIdentifier(Utils.safeParseEventValue(e))
        }
        isValid={!!accountIdentifier}
        placeholder='e.g. xy12345.us-east-1'
      />
      <InputGroup
        title='Warehouse'
        noMargin
        inputProps={{
          className: 'w-100',
          name: 'warehouse',
        }}
        value={warehouse}
        onChange={(e: InputEvent) => setWarehouse(Utils.safeParseEventValue(e))}
        placeholder='COMPUTE_WH'
      />
      <InputGroup
        title='Database'
        noMargin
        inputProps={{
          className: 'w-100',
          name: 'database',
        }}
        value={database}
        onChange={(e: InputEvent) => setDatabase(Utils.safeParseEventValue(e))}
        placeholder='FLAGSMITH'
      />
      <InputGroup
        title='Schema'
        noMargin
        inputProps={{
          className: 'w-100',
          name: 'schema',
        }}
        value={schema}
        onChange={(e: InputEvent) => setSchema(Utils.safeParseEventValue(e))}
        placeholder='ANALYTICS'
      />
      <InputGroup
        title='Role'
        noMargin
        inputProps={{
          className: 'w-100',
          name: 'role',
        }}
        value={role}
        onChange={(e: InputEvent) => setRole(Utils.safeParseEventValue(e))}
        placeholder='FLAGSMITH_LOADER'
      />
      <InputGroup
        title='User'
        noMargin
        inputProps={{
          className: 'w-100',
          name: 'user',
        }}
        value={user}
        onChange={(e: InputEvent) => setUser(Utils.safeParseEventValue(e))}
        placeholder='FLAGSMITH_SERVICE'
      />
      {error && (
        <ErrorMessage
          error={`Failed to ${
            isEdit ? 'update' : 'create'
          } warehouse connection. Please try again.`}
        />
      )}
      <div className='text-right mt-2'>
        <Button type='submit' disabled={isSaving || !isValid || !hasChanges}>
          {getButtonLabel(isEdit, isSaving)}
        </Button>
      </div>
    </form>
  )
}

CreateWarehouseConnectionModal.displayName = 'CreateWarehouseConnectionModal'
export default CreateWarehouseConnectionModal
