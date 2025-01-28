import { FC, useCallback, useState } from 'react'
import {
  deleteChangeRequest,
  useGetChangeRequestsQuery,
} from 'common/services/useChangeRequest'
import ConfigProvider from 'common/providers/ConfigProvider'
import Utils from 'common/utils/utils'
import Button from './base/forms/Button'
import { getStore } from 'common/store'
import {
  useGetProjectChangeRequestQuery,
  useGetProjectChangeRequestsQuery,
} from 'common/services/useProjectChangeRequest'

type DeleteAllChangeRequestsType = {
  environmentId: string
  projectId: string
}

const DeleteAllChangeRequests: FC<DeleteAllChangeRequestsType> = ({
  environmentId,
  projectId,
}) => {
  const hasFeature = Utils.getFlagsmithHasFeature('delete_all_change_requests')
  const { data, refetch } = useGetChangeRequestsQuery(
    {
      committed: false,
      environmentId,
      page: 1,
      page_size: 100,
    },
    { refetchOnMountOrArgChange: true },
  )
  const [isSaving, setIsSaving] = useState(false)

  const deleteAllChangeRequests = useCallback(() => {
    setIsSaving(true)
    Promise.all(
      data!.results.map((changeRequest) => {
        return deleteChangeRequest(getStore(), { id: changeRequest.id }, {c})
      }),
    ).then(() => {
      setIsSaving(false)
    })
  }, [data])
  console.log(data)
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
