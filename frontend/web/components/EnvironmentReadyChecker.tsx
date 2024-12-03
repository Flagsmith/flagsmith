import { FC, useEffect, useState } from 'react'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'

type EnvironmentReadyCheckerType = {
  match: {
    params: {
      environmentId?: string
    }
  }
}

const EnvironmentReadyChecker: FC<EnvironmentReadyCheckerType> = ({
  children,
  match,
}) => {
  const [environmentCreated, setEnvironmentCreated] = useState(false)

  const { data, isLoading } = useGetEnvironmentQuery(
    {
      id: match.params.environmentId,
    },
    {
      pollingInterval: 1000,
      skip: !match.params.environmentId || environmentCreated,
    },
  )
  useEffect(() => {
    if (!!data && !data?.is_creating) {
      setEnvironmentCreated(true)
    }
  }, [data])
  if (!match?.params?.environmentId) {
    return children
  }
  return isLoading ? (
    <div className='text-center'>
      <Loader />
    </div>
  ) : data?.is_creating ? (
    <div className='container'>
      <div className='d-flex flex-column h-100 flex-1 justify-content-center align-items-center'>
        <Loader />
        <h3>Preparing your environment</h3>
        <p>We are setting up your new environment...</p>
      </div>
    </div>
  ) : (
    children
  )
}

export default EnvironmentReadyChecker
