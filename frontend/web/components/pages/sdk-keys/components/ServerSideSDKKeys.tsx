import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Tooltip from 'components/Tooltip'
import Constants from 'common/constants'
import { useHasPermission } from 'common/providers/Permission'
import { EnvironmentPermission } from 'common/types/permissions.types'
import CreateServerSideKeyModal from './CreateServerSideKeyModal'
import ServerSideKeyRow from './ServerSideKeyRow'
import { useServerSideKeys } from 'components/pages/sdk-keys/hooks/useServerSideKeys'

type ServerSideKey = {
  id: string
  key: string
  name: string
}

type ServerSideSDKKeysProps = {
  environmentId: string
  environmentName: string
}

const ServerSideSDKKeys: FC<ServerSideSDKKeysProps> = ({
  environmentId,
  environmentName,
}) => {
  const { permission: isAdmin } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: EnvironmentPermission.ADMIN,
  })

  const { handleCreateKey, handleRemove, isDeletingKey, isLoading, keys } =
    useServerSideKeys({ environmentId })

  const handleCreate = () => {
    openModal(
      'Create Server-side Environment Keys',
      <CreateServerSideKeyModal
        environmentName={environmentName}
        onSubmit={handleCreateKey}
      />,
      'p-0',
    )
  }

  const filterByName = (item: ServerSideKey, search: string) =>
    item.name.toLowerCase().includes(search.toLowerCase())

  const renderKeyRow = ({ id, key, name }: ServerSideKey) => (
    <ServerSideKeyRow
      id={id}
      keyValue={key}
      name={name}
      isDeleting={isDeletingKey(id)}
      onRemove={handleRemove}
    />
  )

  return (
    <FormGroup className='my-4'>
      <div className='col-md-6'>
        <h5 className='mb-2'>Server-side Environment Keys</h5>
        <p className='fs-small lh-sm mb-0'>
          Flags can be evaluated locally within your own Server environments
          using our{' '}
          <Button
            theme='text'
            href='https://docs.flagsmith.com/clients/overview#server-side-sdks'
            target='_blank'
          >
            Server-side Environment Keys
          </Button>
          .
        </p>
        <p className='fs-small lh-sm mb-0'>
          Server-side SDKs should be initialised with a Server-side Environment
          Key.
        </p>
        {isAdmin ? (
          <Button onClick={handleCreate} className='my-4'>
            Create Server-side Environment Key
          </Button>
        ) : (
          <Tooltip
            title={
              <Button className='my-4' disabled>
                Create Server-side Environment Key
              </Button>
            }
            place='right'
          >
            {Constants.environmentPermissions(EnvironmentPermission.ADMIN)}
          </Tooltip>
        )}
      </div>
      {isLoading && (
        <div className='text-center'>
          <Loader />
        </div>
      )}
      {keys && !!keys.length && (
        <PanelSearch
          id='server-side-keys-list'
          title='Server-side Environment Keys'
          className='no-pad'
          items={keys}
          filterRow={filterByName}
          renderRow={renderKeyRow}
        />
      )}
    </FormGroup>
  )
}

export default ServerSideSDKKeys
