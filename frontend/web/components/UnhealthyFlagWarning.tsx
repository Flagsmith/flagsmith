import { FC } from 'react'
import Constants from 'common/constants'
import { ProjectFlag } from 'common/types/responses'
import { IonIcon } from '@ionic/react'
import { warning } from 'ionicons/icons'
import { useGetTagsQuery } from 'common/services/useTag'
import { useGetHealthEventsQuery } from 'common/services/useHealthEvents'

type UnhealthyFlagWarningType = {
  projectFlag: ProjectFlag
}

const UnhealthyFlagWarning: FC<UnhealthyFlagWarningType> = ({
  projectFlag,
}) => {
  const { data: tags } = useGetTagsQuery(
    { projectId: String(projectFlag.project) },
    { refetchOnFocus: false, skip: !projectFlag?.project },
  )
  const { data: healthEvents } = useGetHealthEventsQuery(
    { projectId: String(projectFlag.project) },
    { refetchOnFocus: false, skip: !projectFlag?.project },
  )
  const unhealthyTagId = tags?.find((tag) => tag.type === 'UNHEALTHY')?.id
  const latestHealthEvent = healthEvents?.find(
    (event) => event.feature === projectFlag.id,
  )

  if (
    !unhealthyTagId ||
    !projectFlag?.tags?.includes(unhealthyTagId) ||
    latestHealthEvent?.type !== 'UNHEALTHY'
  )
    return null

  return (
    <div className='fs-caption' style={{ color: Constants.tagColors[16] }}>
      {/* TODO: Provider info and link to issue will be provided by reason via the API */}
      {latestHealthEvent.reason}
      {latestHealthEvent.reason && (
        <IonIcon style={{ marginBottom: -2 }} className='ms-1' icon={warning} />
      )}
    </div>
  )
}

export default UnhealthyFlagWarning
