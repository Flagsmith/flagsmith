import type { FetchBaseQueryError } from '@reduxjs/toolkit/query'
import type { SerializedError } from '@reduxjs/toolkit'
import {
  useActionChangeRequestMutation,
  useDeleteChangeRequestMutation,
  useGetChangeRequestQuery,
  useUpdateChangeRequestAssigneesMutation,
} from 'common/services/useChangeRequest'
import type { ChangeRequestDetail, ChangeRequestDetailParams } from './types'

type RequestError = FetchBaseQueryError | SerializedError | undefined

const hasDetail = (data: unknown): data is { detail: string } =>
  typeof data === 'object' &&
  data !== null &&
  'detail' in data &&
  typeof data.detail === 'string'

// Match the Flux store, which shows the API's detail message on its own
const toErrorMessage = (error: RequestError) => {
  if (error && 'data' in error && hasDetail(error.data)) {
    return error.data.detail
  }
  return error
}

export const useRtkChangeRequestDetail = ({
  enabled,
  environmentId,
  id,
  projectId,
}: ChangeRequestDetailParams): ChangeRequestDetail => {
  const {
    data,
    error: loadError,
    isFetching,
  } = useGetChangeRequestQuery(
    { environmentId, id, projectId },
    // Like the Flux store, refetch after an action, not on window focus
    { refetchOnFocus: false, skip: !enabled },
  )
  const [action, actionState] = useActionChangeRequestMutation()
  const [updateAssignees, updateState] =
    useUpdateChangeRequestAssigneesMutation()
  const [deleteChangeRequest, deleteState] = useDeleteChangeRequestMutation()

  const isUpdating =
    isFetching ||
    actionState.isLoading ||
    updateState.isLoading ||
    deleteState.isLoading
  const error =
    actionState.error || updateState.error || deleteState.error || loadError

  return {
    approve: () => {
      action({ actionType: 'approve', id })
    },
    changeRequest: data?.changeRequest,
    commit: async (onDone) => {
      const res = await action({ actionType: 'commit', id })
      if (!('error' in res)) onDone()
    },
    environmentFlag: data?.environmentFlag,
    error: toErrorMessage(error),
    isUpdating,
    notFound:
      !data && !!loadError && 'status' in loadError && loadError.status === 404,
    projectFlag: data?.projectFlag,
    remove: async (onDone) => {
      const res = await deleteChangeRequest({ id: Number(id) })
      if (!('error' in res)) onDone()
    },
    updateAssignees: (assignees) => {
      if (isUpdating || !data) return
      updateAssignees({ ...assignees, id })
    },
  }
}
