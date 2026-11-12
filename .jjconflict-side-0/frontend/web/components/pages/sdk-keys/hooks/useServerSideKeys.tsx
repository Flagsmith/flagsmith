import React from 'react'
import {
  useCreateServersideEnvironmentKeysMutation,
  useDeleteServersideEnvironmentKeysMutation,
  useGetServersideEnvironmentKeysQuery,
} from 'common/services/useServersideEnvironmentKey'

type UseServerSideKeysParams = {
  environmentId: string
}

export const useServerSideKeys = ({
  environmentId,
}: UseServerSideKeysParams) => {
  const { data: keys, isLoading } = useGetServersideEnvironmentKeysQuery(
    { environmentId },
    { skip: !environmentId },
  )

  const [createKey] = useCreateServersideEnvironmentKeysMutation()
  const [deleteKey, { isLoading: isDeleting, originalArgs: deleteArgs }] =
    useDeleteServersideEnvironmentKeysMutation()

  const handleCreateKey = async (name: string) => {
    await createKey({ data: { name }, environmentId }).unwrap()
    closeModal()
  }

  const handleRemove = (id: string, name: string) => {
    openConfirm({
      body: (
        <div>
          Are you sure you want to remove the SDK key <strong>{name}</strong>?
          This action cannot be undone.
        </div>
      ),
      destructive: true,
      onYes: () => {
        deleteKey({ environmentId, id })
      },
      title: 'Delete Server-side Environment Keys',
      yesText: 'Confirm',
    })
  }

  const isDeletingKey = (id: string) => isDeleting && deleteArgs?.id === id

  return {
    handleCreateKey,
    handleRemove,
    isDeletingKey,
    isLoading,
    keys,
  }
}
