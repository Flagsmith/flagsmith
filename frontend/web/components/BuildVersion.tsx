import { FC, useEffect, useState } from 'react'
import getBuildVersion from 'project/getBuildVersion'
import { IonIcon } from '@ionic/react'
import { pricetag } from 'ionicons/icons'

type BuildVersionType = {}
type Version = {
  tag: string
  backend_sha: string
  frontend_sha: string
}
const BuildVersion: FC<BuildVersionType> = ({}) => {
  const [version, setVersion] = useState<Version>()

  useEffect(() => {
    getBuildVersion().then((version: Version) => {
      setVersion(version)
    })
  }, [])
  return (
    <div className='text-muted position-fixed bottom-0 p-2 fs-caption'>
      {version?.tag !== 'Unknown' && (
        <Tooltip
          html
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
            version?.frontend_sha !== 'Unknown'
              ? `Frontend SHA: ${version?.frontend_sha}`
              : ''
          }${
            version?.backend_sha !== 'Unknown'
              ? `${
                  version?.frontend_sha !== 'Unknown' ? '<br/>' : ''
                }Backend SHA: ${version?.backend_sha}`
              : ''
          }`}
        </Tooltip>
      )}
    </div>
  )
}

export default BuildVersion
