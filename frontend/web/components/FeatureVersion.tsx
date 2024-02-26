import { FC } from 'react'
import DiffFeature from './diff/DiffFeature'
import { useGetVersionFeatureStateQuery } from 'common/services/useVersionFeatureState'

type VersionDiffType = {
  oldUUID: string
  newUUID: string
  environmentId: string
  projectId: string
  featureId: number
}

const FeatureVersion: FC<VersionDiffType> = ({
  environmentId,
  featureId,
  newUUID,
  oldUUID,
  projectId,
}) => {
  const { data: oldData } = useGetVersionFeatureStateQuery({
    environmentId,
    featureId,
    sha: oldUUID,
  })
  const { data: newData } = useGetVersionFeatureStateQuery({
    environmentId,
    featureId,
    sha: newUUID,
  })
  return (
    <div className='p-2'>
      {!oldData || !newData ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
        <DiffFeature
          projectId={projectId}
          featureId={featureId}
          oldState={oldData}
          newState={newData}
        />
      )}
    </div>
  )
}

export default FeatureVersion
