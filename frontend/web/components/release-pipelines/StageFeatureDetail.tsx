import { useGetProfileQuery } from 'common/services/useProfile'
import { getProjectFlag } from 'common/services/useProjectFlag'
import { getStore } from 'common/store'
import { ProjectFlag } from 'common/types/responses'
import { useCallback, useEffect, useState } from 'react'
type StageFeatureDetailProps = {
  features: number[]
  publishedBy?: number
  projectId: string
}

const StageFeatureDetail = ({
  features,
  projectId,
  publishedBy,
}: StageFeatureDetailProps) => {
  const [projectFlags, setProjectFlags] = useState<ProjectFlag[]>([])

  const { data: userData } = useGetProfileQuery(
    { id: publishedBy },
    {
      skip: !publishedBy,
    },
  )

  const getProjectFlags = useCallback(async () => {
    if (!features.length) {
      return
    }

    try {
      const res = await Promise.all(
        features.map((id) =>
          getProjectFlag(getStore(), {
            id: `${id}`,
            project: projectId,
          }),
        ),
      )
      const projectFlags = res.map((r) => r.data)
      setProjectFlags(projectFlags)
    } catch (error) {
      console.error(error)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [features?.join(','), projectId])

  useEffect(() => {
    getProjectFlags()
  }, [getProjectFlags])

  if (!features.length) {
    return (
      <>
        <h6>Features (0)</h6>
        <p className='text-muted'>No features at this stage.</p>
      </>
    )
  }

  return (
    <>
      <h6>Features ({features.length})</h6>
      {projectFlags?.map((flag) => (
        <>
          <div key={flag.id} className='text-muted'>
            <b>{flag.name}</b>
          </div>
          {userData?.first_name && (
            <div className='text-muted text-small mt-1'>
              Added by {userData?.first_name} {userData?.last_name}
            </div>
          )}
        </>
      ))}
    </>
  )
}

export default StageFeatureDetail
