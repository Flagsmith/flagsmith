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
  switch (level) {
    case 'identity': {
      return (
        hasUserOverride && (
          <>
            {Utils.renderWithPermission(
              permission,
              permissionDescription,
              <Button
                theme='text'
                size='xSmall'
                disabled={!permission}
                onClick={() => {
                  removeUserOverride({
                    environmentId,
                    identifier: identifier!,
                    identity: identity!,
                    identityFlag: overrideFeatureState as IdentityFeatureState,
                    projectFlag: projectFlag!,
                  })
                }}
              >
                <Icon name='refresh' fill='#6837FC' width={16} /> Reset
              </Button>,
            )}
          </>
        )
      )
    }
    default:
      return null
  }
  return <></>
}

export default FeatureOverrideCTA
