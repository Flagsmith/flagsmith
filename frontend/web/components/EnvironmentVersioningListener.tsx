import { FC, useEffect } from 'react'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'
import { Environment } from 'common/types/responses'

type EnvironmentVersioningListenerType = {
  id: number
  versioningEnabled: boolean
  onChange: () => void
}

const EnvironmentVersioningListener: FC<EnvironmentVersioningListenerType> = ({
  id,
  onChange,
  versioningEnabled,
}) => {
  const { data, isFetching, isSuccess } = useGetEnvironmentQuery(
    { id: `${id}` },
    {
      pollingInterval: versioningEnabled ? undefined : 2000,
      skip: versioningEnabled || !id,
    },
  )
  useEffect(() => {
    if (isFetching || !id) {
      return
    }
    if (data?.use_v2_feature_versioning && !versioningEnabled) {
      onChange()
    }
  }, [id, isFetching, data, isSuccess])
  return null
}

export default EnvironmentVersioningListener
