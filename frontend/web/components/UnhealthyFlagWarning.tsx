import { FC } from 'react'
import Constants from 'common/constants'
import { HealthEvent } from 'common/types/responses'
import { IonIcon } from '@ionic/react'
import { warning } from 'ionicons/icons'

type UnhealthyFlagWarningType = {
  featureUnhealthyEvents?: HealthEvent[]
  onClick?: (e?: React.MouseEvent) => void
}

const UnhealthyFlagWarning: FC<UnhealthyFlagWarningType> = ({
  featureUnhealthyEvents,
  onClick,
}) => {
  if (!featureUnhealthyEvents?.length) return null

  return (
    <Tooltip
      title={
        <div
          className='fs-caption'
          style={{ color: Constants.featureHealth.unhealthyColor }}
          onClick={onClick}
        >
          <div>
            This feature has {featureUnhealthyEvents?.length} active alert
            {featureUnhealthyEvents?.length > 1 ? 's' : ''}. Check them in the
            'Feature Health' tab.
            <IonIcon
              style={{ marginBottom: -2 }}
              className='ms-1'
              icon={warning}
            />
          </div>
        </div>
      }
    >
      This feature is tagged as unhealthy in one or more environments.
    </Tooltip>
  )
}

export default UnhealthyFlagWarning
