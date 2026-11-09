import { useEffect, useState } from 'react'
import AppActions from 'common/dispatcher/app-actions'
import ChangeRequestStore from 'common/stores/change-requests-store'
import {
  ChangeRequest,
  FeatureState,
  ProjectFlag,
} from 'common/types/responses'
import type { ChangeRequestDetail, ChangeRequestDetailParams } from './types'

type FluxFlags = Record<
  string,
  { environmentFlag: FeatureState; projectFlag: ProjectFlag } | undefined
>

export const useFluxChangeRequestDetail = ({
  enabled,
  environmentId,
  id,
  projectId,
}: ChangeRequestDetailParams): ChangeRequestDetail => {
  const [, setUpdate] = useState(0)

  useEffect(() => {
    if (!enabled) return
    AppActions.getChangeRequest(id, projectId, environmentId)
  }, [enabled, id, projectId, environmentId])

  useEffect(() => {
    if (!enabled) return
    const forceUpdate = () => setUpdate(Date.now())
    ChangeRequestStore.on('change', forceUpdate)
    return () => {
      ChangeRequestStore.off('change', forceUpdate)
    }
  }, [enabled])

  const models: Record<string, ChangeRequest | undefined> =
    ChangeRequestStore.model
  const flags: FluxFlags = ChangeRequestStore.flags
  const changeRequest = models[id]
  const error = ChangeRequestStore.error

  return {
    approve: () => AppActions.actionChangeRequest(id, 'approve'),
    changeRequest,
    commit: (onDone) => AppActions.actionChangeRequest(id, 'commit', onDone),
    environmentFlag: flags[id]?.environmentFlag,
    error,
    isUpdating: ChangeRequestStore.isLoading,
    notFound: !!error && !changeRequest,
    projectFlag: flags[id]?.projectFlag,
    remove: (onDone) => AppActions.deleteChangeRequest(id, onDone),
    updateAssignees: ({ approvals, group_assignments }) => {
      if (ChangeRequestStore.isLoading || !changeRequest) return
      AppActions.updateChangeRequest({
        approvals,
        description: changeRequest.description,
        feature_states: changeRequest.feature_states,
        group_assignments,
        id: changeRequest.id,
        title: changeRequest.title,
      })
    },
  }
}
