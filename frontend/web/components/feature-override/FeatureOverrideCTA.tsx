import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import { removeUserOverride } from 'components/RemoveUserOverride'
import Icon from 'components/Icon'

type FeatureOverrideCTAType = {
  level: 'identity' | 'segment'
  hasUserOverride: boolean
}

const FeatureOverrideCTA: FC<FeatureOverrideCTAType> = ({
  hasUserOverride,
  level,
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
                    identifier: identity.identity.identifier,
                    identity: id,
                    identityFlag,
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
  }
  return <></>
}

export default FeatureOverrideCTA
