import React, { FC, ReactNode, useEffect, useState } from 'react'
import { useHistory, useRouteMatch } from 'react-router-dom'
import { sortBy } from 'lodash'

import Constants from 'common/constants'
import useDebouncedSearch from 'common/useDebouncedSearch'
import { Environment } from 'common/types/responses'
import {
  useDeleteSegmentMutation,
  useGetSegmentsQuery,
} from 'common/services/useSegment'
import { useHasPermission } from 'common/providers/Permission'
import API from 'project/api'
import Button from 'components/base/forms/Button'
import CreateSegmentModal from 'components/modals/CreateSegment'
import PanelSearch from 'components/PanelSearch'
import JSONReference from 'components/JSONReference'

import Utils from 'common/utils/utils'
import ProjectStore from 'common/stores/project-store'
import PageTitle from 'components/PageTitle'
import Switch from 'components/Switch'
import classNames from 'classnames'
import InfoMessage from 'components/InfoMessage'

import CodeHelp from 'components/CodeHelp'
import SegmentRow from 'components/segments/SegmentRow/SegmentRow'

const SegmentsPage: FC = () => {
  const history = useHistory()
  const route = useRouteMatch<{ environmentId: string; projectId: string }>()

  const { projectId } = route.params
  const environmentId = (
    ProjectStore.getEnvironment() as unknown as Environment | undefined
  )?.api_key
  const params = Utils.fromParam()
  const id = params.id
  const { search, searchInput, setSearchInput } = useDebouncedSearch('')
  const [page, setPage] = useState(1)
  const [showFeatureSpecific, setShowFeatureSpecific] = useState(
    params.featureSpecific === 'true',
  )

  useEffect(() => {
    if (id) {
      history.push(id, !manageSegmentsPermission)
    } else if (!id && typeof closeModal !== 'undefined') {
      closeModal()
    }
  }, [id])

  const { data, error, isLoading, refetch } = useGetSegmentsQuery({
    include_feature_specific: showFeatureSpecific,
    page,
    page_size: 100,
    projectId,
    q: search,
  })
  const [_, { isLoading: isRemoving }] = useDeleteSegmentMutation()

  const segmentsLimitAlert = Utils.calculateRemainingLimitsPercentage(
    ProjectStore.getTotalSegments(),
    ProjectStore.getMaxSegmentsAllowed(),
  )

  useEffect(() => {
    API.trackPage(Constants.pages.FEATURES)
  }, [])
  useEffect(() => {
    if (error) {
      // Kick user back out to projects
      history.replace(Utils.getOrganisationHomePage())
    }
  }, [error, history])

  useEffect(() => {
    history.replace(
      `${document.location.pathname}?${Utils.toParam({
        ...Utils.fromParam(),
        featureSpecific: showFeatureSpecific,
      })}`,
    )
  }, [showFeatureSpecific, history])

  const newSegment = () => {
    openModal(
      'New Segment',
      <CreateSegmentModal
        onComplete={() => {
          closeModal()
        }}
        environmentId={environmentId!}
        projectId={projectId}
      />,
      'side-modal create-new-segment-modal',
    )
  }

  const { permission: manageSegmentsPermission } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'MANAGE_SEGMENTS',
  })

  const renderWithPermission = (
    permission: boolean,
    name: string,
    el: ReactNode,
  ) => {
    return permission ? (
      el
    ) : (
      <Tooltip title={el} place='right'>
        {Constants.projectPermissions('Manage segments')}
      </Tooltip>
    )
  }

  const segments = data?.results
  return (
    <div
      data-test='segments-page'
      id='segments-page'
      className='app-container container'
    >
      <PageTitle
        cta={
          <>
            {renderWithPermission(
              manageSegmentsPermission,
              'Manage segments',
              <Button
                disabled={
                  !manageSegmentsPermission ||
                  segmentsLimitAlert.percentage >= 100
                }
                id='show-create-segment-btn'
                data-test='show-create-segment-btn'
                onClick={newSegment}
              >
                Create Segment
              </Button>,
            )}
          </>
        }
        title={'Segments'}
      >
        Create and manage groups of identities with similar{' '}
        <Button
          theme='text'
          href='https://docs.flagsmith.com/basic-features/managing-identities#identity-traits'
          target='_blank'
        >
          traits
        </Button>
        . Segments can be used to override features within the features page for
        any environment.{' '}
        <Button
          theme='text'
          target='_blank'
          href='https://docs.flagsmith.com/basic-features/segments'
          className='fw-normal'
        >
          Learn more.
        </Button>
      </PageTitle>
      <div className='segments-page'>
        {isLoading && !segments && !searchInput && (
          <div className='centered-container'>
            <Loader />
          </div>
        )}
        {(!isLoading || segments || searchInput) && (
          <div>
            {Utils.displayLimitAlert('segments', segmentsLimitAlert.percentage)}
            <div>
              <FormGroup className={classNames({ 'opacity-50': isRemoving })}>
                <PanelSearch
                  filterElement={
                    <div className='text-right me-2'>
                      <label className='me-2'>Include Feature-Specific</label>
                      <Switch
                        checked={showFeatureSpecific}
                        onChange={setShowFeatureSpecific}
                      />
                    </div>
                  }
                  renderSearchWithNoResults
                  className='no-pad'
                  id='segment-list'
                  renderFooter={() => (
                    <JSONReference
                      className='mx-2 mt-4'
                      title={'Segments'}
                      json={segments}
                    />
                  )}
                  items={sortBy(segments, (v) => {
                    return `${v.feature ? 'a' : 'z'}${v.name}`
                  })}
                  renderRow={(segment, index) => {
                    return renderWithPermission(
                      manageSegmentsPermission,
                      'Manage segments',
                      <SegmentRow
                        segment={segment}
                        index={index}
                        projectId={projectId}
                      />,
                    )
                  }}
                  paging={data}
                  nextPage={() => setPage(page + 1)}
                  prevPage={() => setPage(page - 1)}
                  goToPage={(page: number) => setPage(page)}
                  search={searchInput}
                  onChange={(e: any) => {
                    setSearchInput(Utils.safeParseEventValue(e))
                  }}
                  filterRow={() => true}
                />
              </FormGroup>

              <InfoMessage collapseId={'segment-identify'}>
                Segments require you to identify users, setting traits will add
                users to segments.
              </InfoMessage>
              <FormGroup className='mt-4'>
                <CodeHelp
                  title='Using segments'
                  snippets={Constants.codeHelp.USER_TRAITS(
                    environmentId || 'ENVIRONMENT_KEY',
                  )}
                />
              </FormGroup>
            </div>
          </div>
        )}
        <FormGroup>
          <CodeHelp
            title='Managing user traits and segments'
            snippets={Constants.codeHelp.USER_TRAITS(environmentId || '')}
          />
        </FormGroup>
      </div>
    </div>
  )
}

export default SegmentsPage
