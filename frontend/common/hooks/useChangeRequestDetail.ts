import {
  ChangeRequest,
  FeatureState,
  ProjectFlag,
} from 'common/types/responses'
import {
  useActionChangeRequestMutation,
  useDeleteChangeRequestMutation,
  useGetChangeRequestQuery,
  useUpdateChangeRequestAssigneesMutation,
} from 'common/services/useChangeRequest'
import { isNotFoundError, toErrorMessage } from 'common/utils/requestError'

export type ChangeRequestAssignees = Pick<
  ChangeRequest,
  'approvals' | 'group_assignments'
>

type ChangeRequestDetailParams = {
  environmentId: string
  id: string
  projectId: string
}

export type ChangeRequestDetail = {
  changeRequest?: ChangeRequest
  environmentFlag?: FeatureState
  projectFlag?: ProjectFlag
  error?: unknown
  isUpdating: boolean
  notFound: boolean
  approve: () => void
  commit: (onDone: () => void) => void
  remove: (onDone: () => void) => void
  updateAssignees: (assignees: ChangeRequestAssignees) => void
}

export const useChangeRequestDetail = ({
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
    // Refetch after an action, not on window focus
    { refetchOnFocus: false },
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
  // Each mutation keeps its last error, so clear them when a new action starts
  const clearErrors = () => {
    actionState.reset()
    updateState.reset()
    deleteState.reset()
  }

  return {
    approve: () => {
      clearErrors()
      action({ actionType: 'approve', id })
    },
    changeRequest: data?.changeRequest,
    commit: async (onDone) => {
      clearErrors()
      const res = await action({ actionType: 'commit', id })
      if (!('error' in res)) onDone()
    },
    environmentFlag: data?.environmentFlag,
    error: toErrorMessage(error),
    isUpdating,
    notFound: !data && isNotFoundError(loadError),
    projectFlag: data?.projectFlag,
    remove: async (onDone) => {
      clearErrors()
      const res = await deleteChangeRequest({ id: Number(id) })
      if (!('error' in res)) onDone()
    },
    updateAssignees: (assignees) => {
      if (isUpdating || !data) return
      clearErrors()
      updateAssignees({ ...assignees, id })
    },
  }
}
