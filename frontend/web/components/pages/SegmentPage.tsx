import React, { FC } from 'react'
import {
  useDeleteSegmentMutation,
  useGetSegmentQuery,
} from 'common/services/useSegment'
import { useHistory, useRouteMatch } from 'react-router-dom'
import CreateSegment from 'components/modals/CreateSegment'
import ProjectStore from 'common/stores/project-store'
import { Environment } from 'common/types/responses'
import ChangeRequestStore from 'common/stores/change-requests-store'
import Breadcrumb from 'components/Breadcrumb'
import PageTitle from 'components/PageTitle'
import Button from 'components/base/forms/Button'
import { useHasPermission } from 'common/providers/Permission'
import { handleRemoveSegment } from 'components/segments/SegmentRow/SegmentRow'
import { removeIdentity } from './UsersPage'
import Icon from 'components/Icon'

type SegmentPageType = {}

const SegmentPage: FC<SegmentPageType> = ({}) => {
  const route = useRouteMatch<{ id: string; projectId: string }>()
  const { id, projectId } = route.params
  const history = useHistory()
  const environmentId = (
    ProjectStore.getEnvironment() as unknown as Environment | undefined
  )?.api_key
  const { data: segment } = useGetSegmentQuery({ id, projectId })

  const { permission: manageSegmentsPermission } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'MANAGE_SEGMENTS',
  })

  const [removeSegment] = useDeleteSegmentMutation()
  const onRemoveSegment = () => {
    handleRemoveSegment(projectId, segment!, removeSegment, () => {
      history.replace(`/project/${projectId}/segments`)
    })
  }
  return (
    <div
      style={{ opacity: ChangeRequestStore.isLoading ? 0.25 : 1 }}
      data-test='segment-page'
      id='segment-page'
      className='app-container container-fluid mt-3'
    >
      <Breadcrumb
        items={[
          {
            title: 'Segments',
            url: `/project/${projectId}/segments/`,
          },
        ]}
        currentPage={segment?.name}
      />
      <PageTitle
        cta={
          manageSegmentsPermission && (
            <Row>
              <Button
                data-test='remove-segment-btn'
                className='btn btn-with-icon'
                type='button'
                onClick={onRemoveSegment}
              >
                <Icon name='trash-2' width={20} fill='#656D7B' />
              </Button>
            </Row>
          )
        }
        title={segment?.name}
      >
        {segment?.description}
      </PageTitle>

      <CreateSegment
        segment={parseInt(id)}
        readOnly={!manageSegmentsPermission}
        projectId={projectId}
        environmentId={environmentId!}
      />
    </div>
  )
}

export default SegmentPage
