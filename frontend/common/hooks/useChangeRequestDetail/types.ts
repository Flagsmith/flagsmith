import {
  ChangeRequest,
  FeatureState,
  ProjectFlag,
} from 'common/types/responses'

export type ChangeRequestAssignees = Pick<
  ChangeRequest,
  'approvals' | 'group_assignments'
>

export type ChangeRequestDetailParams = {
  environmentId: string
  id: string
  projectId: string
  enabled: boolean
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
