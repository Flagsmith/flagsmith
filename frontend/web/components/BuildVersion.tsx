import { FC } from 'react'
import { IonIcon } from '@ionic/react'
import { pricetag } from 'ionicons/icons'
import {
  defaultVersionTag,
  useGetBuildVersionQuery,
} from 'common/services/useBuildVersion'

type BuildVersionType = {}

const BuildVersion: FC<BuildVersionType> = ({}) => {
  const { data: version } = useGetBuildVersionQuery({})
  return (
    <>
      {version?.tag !== defaultVersionTag && (
        <Tooltip
          title={
            <span>
              <span className='icon'>
                <IonIcon icon={pricetag} />
              </span>{' '}
              {version?.tag}
            </span>
          }
        >
          {`${
            version?.frontend_sha !== defaultVersionTag
              ? `Frontend SHA: ${version?.frontend_sha}`
              : ''
          }${
            version?.backend_sha !== defaultVersionTag
              ? `${
                  version?.frontend_sha !== defaultVersionTag ? '<br/>' : ''
                }Backend SHA: ${version?.backend_sha}`
              : ''
          }`}
        </Tooltip>
      )}
    </>
  )
}

export default BuildVersion
