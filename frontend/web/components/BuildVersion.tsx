import { FC } from 'react'
import Icon from './icons/Icon'
import {
  defaultVersionTag,
  useGetBuildVersionQuery,
} from 'common/services/useBuildVersion'

type BuildVersionType = {}

const BuildVersion: FC<BuildVersionType> = ({}) => {
  const { data: version } = useGetBuildVersionQuery({})

  return (
    <>
      {version?.tag &&
        version?.tag?.toLowerCase() !== defaultVersionTag?.toLowerCase() && (
          <Tooltip
            title={
              <span>
                <span className='icon'>
                  <Icon name='tag' width={14} />
                </span>{' '}
                {version?.tag}
              </span>
            }
          >
            {`${
              version?.frontend_sha?.toLowerCase() !==
              defaultVersionTag?.toLowerCase()
                ? `Frontend SHA: ${version?.frontend_sha}`
                : ''
            }${
              version?.backend_sha?.toLowerCase() !==
              defaultVersionTag?.toLowerCase()
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
