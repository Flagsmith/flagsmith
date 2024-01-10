import { FC } from 'react'
import { useGetAuditLogItemQuery } from 'common/services/useAuditLogItem'
import ErrorMessage from 'components/ErrorMessage'

type AuditLogItemPageType = {
  match: {
    params: {
      environmentId: string
      projectId: string
      id: string
    }
  }
}

const AuditLogItemPage: FC<AuditLogItemPageType> = ({ match }) => {
  const { data, error, isLoading } = useGetAuditLogItemQuery({
    id: match.params.id,
  })
  return (
    <div>
      {isLoading ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
        <div>
          <ErrorMessage>{error}</ErrorMessage>
        </div>
      )}
    </div>
  )
}

export default AuditLogItemPage
