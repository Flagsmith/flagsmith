import React, { FC } from 'react'
import { useGetSegmentQuery } from 'common/services/useSegment'
import { useHistory, useRouteMatch } from 'react-router-dom'
import CreateSegment from 'components/modals/CreateSegment'
import ProjectStore from 'common/stores/project-store'
import { Environment } from 'common/types/responses'
import ChangeRequestStore from 'common/stores/change-requests-store'
import Breadcrumb from 'components/Breadcrumb'
import Button from 'components/base/forms/Button'
import { useHasPermission } from 'common/providers/Permission'
import Icon from 'components/Icon'
import { handleRemoveSegment } from 'components/modals/ConfirmRemoveSegment'
import SegmentSelect from 'components/SegmentSelect'
import Utils from 'common/utils/utils'

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

  const onRemoveSegment = () => {
    handleRemoveSegment(projectId, segment!, () => {
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
        isCurrentPageMuted={false}
        currentPage={
          <div className='d-flex flex-1 align-items-center justify-content-between'>
            <span style={{ width: 180 }} className='d-inline-block'>
              <SegmentSelect
                onChange={(v) =>
                  history.replace(
                    `/project/${projectId}/segments/${v.value}?${Utils.toParam(
                      Utils.fromParam(),
                    )}`,
                  )
                }
                className='react-select select-xsm'
                value={parseInt(id)}
                projectId={projectId}
              />
            </span>
            {Utils.renderWithPermission(
              manageSegmentsPermission,
              'Manage Segments',
              <Button
                data-test='remove-segment-btn'
                className='btn btn-with-icon'
                type='button'
                disabled={!manageSegmentsPermission}
                onClick={onRemoveSegment}
              >
                <Icon name='trash-2' width={20} fill='#656D7B' />
              </Button>,
            )}
          </div>
        }
      />

      <div className='mt-3'>
        <CreateSegment
          segment={parseInt(id)}
          readOnly={!manageSegmentsPermission}
          projectId={projectId}
          environmentId={environmentId!}
        />
      </div>
    </div>
  )
}

export default SegmentPage
