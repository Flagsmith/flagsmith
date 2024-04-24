import { FC } from 'react'
import Tag from './tags/Tag'
import Constants from 'common/constants'
import moment from 'moment'
import { Project, ProjectFlag } from 'common/types/responses'
import { getProtectedTags } from 'common/utils/getProtectedTags'
import { IonIcon } from '@ionic/react'
import { close, warning } from 'ionicons/icons'
import Tooltip from './Tooltip'
import ProjectStore from 'common/stores/project-store'

type StaleFlagWarningType = {
  projectFlag: ProjectFlag
}

const StaleFlagWarning: FC<StaleFlagWarningType> = ({ projectFlag }) => {
  const protectedTags = getProtectedTags(projectFlag, `${projectFlag.project}`)
  if (protectedTags?.length) {
    return null
  }
  const created_date = projectFlag?.created_date
  const daysAgo = created_date && moment().diff(moment(created_date), 'days')
  console.log(ProjectStore.model)
  const suggestStale =
    daysAgo >=
    ((ProjectStore.model as Project | null)?.stale_flags_limit_days || 30)
  if (!suggestStale) {
    return null
  }
  return (
    <Tooltip
      title={
        <span
          className='fs-caption d-flex align-items-center'
          style={{ color: Constants.tagColors[2] }}
        >
          Created {daysAgo} days ago
          <IonIcon className='ms-1' icon={warning} />{' '}
        </span>
      }
    >
      You may wish to consider removing this feature or tagging it as permanent.
    </Tooltip>
  )
}

export default StaleFlagWarning
