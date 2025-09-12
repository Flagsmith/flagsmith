import ConfirmRemoveFeature from './modals/ConfirmRemoveFeature'
import React from 'react'
import AppActions from 'common/dispatcher/app-actions'
import {
  FeatureState,
  IdentityFeatureState,
  ProjectFlag,
} from 'common/types/responses'
export const removeUserOverride = ({
  cb,
  environmentId,
  identifier,
  identity,
  identityFlag,
  projectFlag,
}: {
  environmentId: string
  identifier: string
  identity: string
  identityFlag: IdentityFeatureState
  projectFlag: ProjectFlag
  cb?: () => void
}) => {
  const onConfirm = () => {
    AppActions.removeUserFlag({
      cb,
      environmentId,
      identity,
      identityFlag,
    })
  }
  openModal2(
    'Reset User Feature',
    <ConfirmRemoveFeature
      identity={identifier}
      projectFlag={projectFlag}
      cb={onConfirm}
    />,
  )
}
