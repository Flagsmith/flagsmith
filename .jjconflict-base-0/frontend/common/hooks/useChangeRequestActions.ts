import {
  useActionChangeRequestMutation,
  useDeleteChangeRequestMutation,
  useUpdateChangeRequestAssigneesMutation,
} from 'common/services/useChangeRequest'
import { Req } from 'common/types/requests'
import { toErrorMessage } from 'common/utils/requestError'

type ChangeRequestAssignees = Omit<Req['updateChangeRequestAssignees'], 'id'>

export const useChangeRequestActions = (id: string) => {
  const [action, actionState] = useActionChangeRequestMutation()
  const [updateAssignees, updateState] =
    useUpdateChangeRequestAssigneesMutation()
  const [deleteChangeRequest, deleteState] = useDeleteChangeRequestMutation()

  // Each mutation keeps its last error, so clear them when a new action starts
  const clearErrors = () => {
    actionState.reset()
    updateState.reset()
    deleteState.reset()
  }

  return {
    actionError: toErrorMessage(
      actionState.error || updateState.error || deleteState.error,
    ),
    approve: () => {
      clearErrors()
      action({ actionType: 'approve', id })
    },
    // Resolves to whether the publish succeeded
    commit: async () => {
      clearErrors()
      const res = await action({ actionType: 'commit', id })
      return !('error' in res)
    },
    isActing:
      actionState.isLoading || updateState.isLoading || deleteState.isLoading,
    // Resolves to whether the delete succeeded
    remove: async () => {
      clearErrors()
      const res = await deleteChangeRequest({ id: Number(id) })
      return !('error' in res)
    },
    updateAssignees: (assignees: ChangeRequestAssignees) => {
      clearErrors()
      updateAssignees({ ...assignees, id })
    },
  }
}
