import { FC, useCallback, useState } from 'react'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import ConfigProvider from 'common/providers/ConfigProvider'
import Utils from 'common/utils/utils'
import Button from './base/forms/Button'

type DeleteAllChangeRequestsType = {
  environmentId: string
  projectId: string
}

const DeleteAllChangeRequests: FC<DeleteAllChangeRequestsType> = ({
  environmentId,
  projectId,
}) => {
  const hasFeature = Utils.getFlagsmithHasFeature('delete_all_change_requests')
  const { data } = useGetChangeRequestsQuery(
    {
      committed: false,
      environmentId,
      page: 1,
      page_size: 100,
    },
    { refetchOnMountOrArgChange: true, skip: !hasFeature },
  )
  const [isSaving, setIsSaving] = useState(false)

  const deleteAllChangeRequests = useCallback(() => {
    setIsSaving(true)
    Promise.all(data!.results.map((changeRequest)=>{
        return delete
    }))
  }, [data])
  if (!hasFeature) {
    return null
  }
  return (
    <Button
      disabled={isSaving || !data?.results}
      onClick={() => {
        openConfirm({
          body: 'This will remove all change requests.',
          destructive: true,
          onYes: () => {
            deleteAllChangeRequests()
          },
          title: 'Delete variation',
          yesText: 'Confirm',
        })
      }}
    >
      Delete All
    </Button>
  )
}

export default ConfigProvider(DeleteAllChangeRequests)
