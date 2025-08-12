import { getProjectFlag } from 'common/services/useProjectFlag'
import { getStore } from 'common/store'
import { Features, ProjectFlag } from 'common/types/responses'
import { useCallback, useEffect, useState } from 'react'

type StageFeatureDetailProps = {
  features: Features | number[]
  projectId: number
}

const StageFeatureDetail = ({
  features,
  projectId,
}: StageFeatureDetailProps) => {
  const featureIds = Array.isArray(features)
    ? features
    : Object.keys(features || {}).map(Number)
  const [projectFlags, setProjectFlags] = useState<ProjectFlag[]>([])
  const getProjectFlags = useCallback(async () => {
    if (!featureIds.length) {
      return
    }

    try {
      const res = await Promise.all(
        featureIds.map((id) =>
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
  }, [featureIds?.join(','), projectId])

  useEffect(() => {
    getProjectFlags()
  }, [getProjectFlags])

  if (!featureIds.length) {
    return (
      <>
        <h6>Features (0)</h6>
        <p className='text-muted'>No features at this stage.</p>
      </>
    )
  }

  return (
    <>
      <h6>Features ({featureIds.length})</h6>
      {projectFlags?.map((flag) => (
        <p key={flag.id} className='text-muted'>
          <b>{flag.name}</b>
        </p>
      ))}
    </>
  )
}

export default StageFeatureDetail
