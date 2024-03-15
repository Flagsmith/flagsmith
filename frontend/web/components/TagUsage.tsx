import { FC } from 'react'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import WarningMessage from './WarningMessage'

type TagUsageType = {
  projectId: string
  tag: string
}

const TagUsage: FC<TagUsageType> = ({ projectId, tag }) => {
  const { data } = useGetProjectFlagsQuery(
    {
      is_archived: false,
      project: projectId,
      tags: [tag],
    },
    { refetchOnMountOrArgChange: true },
  )
  if (!data?.count) {
    return null
  }
  return (
    <div className='mt-4'>
      <WarningMessage
        warningMessage={`${data?.count} feature${
          data?.count !== 1 ? 's are' : ' is'
        } using this tag.`}
      />
    </div>
  )
}

export default TagUsage
