import { FC } from 'react'
import { useGetOrganisationAuditLogItemQuery } from 'common/services/useAuditLogItem'
import Banner from 'components/base/Banner'
import Button from 'components/base/forms/Button'
import Skeleton from 'components/Skeleton'
import AuditLogChanges from './AuditLogChanges'

type OrganisationAuditLogChangesProps = {
  organisationId: number
  id: number
  versionLimitDays?: number | null
}

// Fetched on expand: the list endpoint has no change_details.
const OrganisationAuditLogChanges: FC<OrganisationAuditLogChangesProps> = ({
  id,
  organisationId,
  versionLimitDays,
}) => {
  const { data, error, isLoading, refetch } =
    useGetOrganisationAuditLogItemQuery({
      id,
      organisationId,
    })
  if (isLoading) {
    return (
      <div
        className='d-flex flex-column gap-2'
        role='status'
        aria-label='Loading changes'
      >
        <Skeleton width={220} />
        <Skeleton width={180} />
      </div>
    )
  }
  if (error || !data) {
    return (
      <Banner
        type='error'
        action={
          <Button theme='outline' size='small' onClick={refetch}>
            Try again
          </Button>
        }
      >
        Couldn't load the changes.
      </Banner>
    )
  }
  return <AuditLogChanges item={data} versionLimitDays={versionLimitDays} />
}

export default OrganisationAuditLogChanges
