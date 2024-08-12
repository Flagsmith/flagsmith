import { FC } from 'react'
import DiffFeature from './diff/DiffFeature'
import { useGetVersionFeatureStateQuery } from 'common/services/useVersionFeatureState'
import InfoMessage from './InfoMessage'
import moment from 'moment'
import { useGetFeatureVersionQuery } from 'common/services/useFeatureVersion'

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
  const { data: oldVersion } = useGetFeatureVersionQuery({
    environmentId,
    featureId: `${featureId}`,
    uuid: oldUUID,
  })
  const { data: newVersion } = useGetFeatureVersionQuery({
    environmentId,
    featureId: `${featureId}`,
    uuid: newUUID,
  })
  const { data: newData } = useGetVersionFeatureStateQuery({
    environmentId,
    featureId,
    sha: newUUID,
  })
  return (
    <div className='p-2'>
      {!oldData || !newData || !oldVersion || !newVersion ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
        <>
          {oldUUID === newUUID ? (
            <InfoMessage>Versions are the same.</InfoMessage>
          ) : (
            <>
              <InfoMessage>
                Comparing{' '}
                <strong>
                  {moment(newVersion.created_at).format('Do MMM YYYY HH:mma')}
                </strong>{' '}
                to{' '}
                <strong>
                  {moment(oldVersion.created_at).format('Do MMM YYYY HH:mma')}
                </strong>
              </InfoMessage>

              <DiffFeature
                environmentId={environmentId}
                projectId={projectId}
                featureId={featureId}
                oldState={oldData}
                newState={newData}
              />
            </>
          )}
        </>
      )}
    </div>
  )
}

export default FeatureVersion
