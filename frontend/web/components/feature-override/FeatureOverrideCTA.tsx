import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import { removeUserOverride } from 'components/RemoveUserOverride'
import Icon from 'components/Icon'
import {
  FeatureState,
  IdentityFeatureState,
  ProjectFlag,
} from 'common/types/responses'
import { useHasPermission } from 'common/providers/Permission'
import Constants from 'common/constants'

type FeatureOverrideCTAType = {
  level: 'identity' | 'segment'
  hasUserOverride: boolean
  projectFlag: ProjectFlag
  environmentId: string
  identity?: string
  identifier?: string
  environmentFeatureState: FeatureState
  overrideFeatureState?: FeatureState | IdentityFeatureState | null
}

const FeatureOverrideCTA: FC<FeatureOverrideCTAType> = ({
  environmentId,
  hasUserOverride,
  identifier,
  identity,
  level,
  overrideFeatureState,
  projectFlag,
}) => {
  const { permission, permissionDescription } =
    Utils.getOverridePermission(level)
  const { permission: hasPermission } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission,
  })
  if (!identity || !identifier || !projectFlag) return null
  switch (level) {
    case 'identity': {
      if (!hasUserOverride) {
        return null
      }
      return (
        <>
          {Utils.renderWithPermission(
            hasPermission,
            Constants.environmentPermissions(permissionDescription),
            <Button
              theme='text'
              size='xSmall'
              disabled={!hasPermission}
              onClick={() => {
                removeUserOverride({
                  environmentId,
                  identifier: identifier,
                  identity: identity,
                  identityFlag: overrideFeatureState as IdentityFeatureState,
                  projectFlag: projectFlag,
                })
              }}
            >
              <Icon name='refresh' fill='#6837FC' width={16} /> Reset
            </Button>,
          )}
        </>
      )
    }
    default:
      return null
  }
}

export default FeatureOverrideCTA
