import { FC, useRef } from 'react'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import WarningMessage from './WarningMessage'
import moment from 'moment'
import {
  useGetProjectChangeRequestQuery,
  useGetProjectChangeRequestsQuery,
} from 'common/services/useProjectChangeRequest'

type ExistingProjectChangeRequestAlertType = {
  projectId: string
  segmentId: string
  className?: string
}

const ExistingProjectChangeRequestAlert: FC<
  ExistingProjectChangeRequestAlertType
> = ({ className, projectId, segmentId }) => {
  const { data } = useGetProjectChangeRequestsQuery({
    committed: false,
    project_id: projectId,
    segment_id: segmentId,
  })

  if (data?.results?.length) {
    return (
      <div className={className}>
        <WarningMessage
          warningMessage={
            'You have open change requests for this segment, please check the Change Requests page.'
          }
        />
      </div>
    )
  }
  return null
}

export default ExistingProjectChangeRequestAlert
