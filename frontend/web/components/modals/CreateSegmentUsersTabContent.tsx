import React, { FC } from 'react'
import moment from 'moment'
import EnvironmentSelect, {
  EnvironmentSelectOption,
} from 'components/EnvironmentSelect'
import PanelSearch from 'components/PanelSearch'
import InfoMessage from 'components/InfoMessage'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import { Res, SegmentMembership } from 'common/types/responses'
import Icon from 'components/icons/Icon'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import {
  identitySegmentService,
  useGetIdentitySegmentsQuery,
} from 'common/services/useIdentitySegment'
import { getStore } from 'common/store'
import { SegmentMembershipEnvBadge } from 'components/segments/SegmentMembershipBadge'
import SegmentMembersList from './SegmentMembersList'

interface CreateSegmentUsersTabContentProps {
  projectId: string | number
  segmentId?: number
  environmentId: string
  setEnvironmentId: (environmentId: string) => void
  identitiesLoading: boolean
  identities: Res['identities'] | undefined
  page: any
  setPage: (page: any) => void
  name: string
  searchInput: string
  setSearchInput: (input: string) => void
  memberships?: SegmentMembership[]
  // When the segment_membership_inspection feature is enabled, the dedicated
  // cursor-paginated members endpoint is used instead of listing every
  // identity and checking membership per row.
  membersEnabled: boolean
}

type UserRowType = {
  id: string
  identifier: string
  segmentName: string
  projectId: string
  index: number
}

const UserRow: FC<UserRowType> = ({
  id,
  identifier,
  index,
  projectId,
  segmentName,
}) => {
  const { data: segments } = useGetIdentitySegmentsQuery({
    identity: id,
    projectId,
  })
  let inSegment = false
  if (segments?.results.find((v) => v.name === segmentName)) {
    inSegment = true
  }
  return (
    <Row key={id} className='list-item list-item-sm clickable'>
      <Row space className='px-3' key={id} data-test={`user-item-${index}`}>
        <div className='font-weight-medium'>{identifier}</div>
        <Row
          className={`font-weight-medium fs-small lh-sm ${
            inSegment ? 'text-primary' : 'faint'
          }`}
        >
          {inSegment ? (
            <>
              <Icon name='checkmark-circle' width={20} fill='#6837FC' />
              <span className='ml-1'>User in segment</span>
            </>
          ) : (
            <>
              <Icon name='minus-circle' width={20} fill='#9DA4AE' />
              <span className='ml-1'>Not in segment</span>
            </>
          )}
        </Row>
      </Row>
    </Row>
  )
}

const CreateSegmentUsersTabContent: React.FC<
  CreateSegmentUsersTabContentProps
> = ({
  environmentId,
  identities,
  identitiesLoading,
  membersEnabled,
  memberships,
  name,
  page,
  projectId,
  searchInput,
  segmentId,
  setEnvironmentId,
  setPage,
  setSearchInput,
}) => {
  const { getEnvironment } = useProjectEnvironments(Number(projectId))

  const membershipByEnvId = React.useMemo(() => {
    const map = new Map<number, SegmentMembership>()
    ;(memberships ?? []).forEach((m) => map.set(m.environment, m))
    return map
  }, [memberships])

  const renderEnvOption = ({ environment, label }: EnvironmentSelectOption) => {
    const membership = environment
      ? membershipByEnvId.get(environment.id)
      : undefined
    return (
      <span className='d-flex align-items-center'>
        <span>{label}</span>
        {environment && membership && (
          <SegmentMembershipEnvBadge
            membership={membership}
            environment={environment}
          />
        )}
      </span>
    )
  }

  const selectedEnv = React.useMemo(
    () => getEnvironment(environmentId) ?? null,
    [environmentId, getEnvironment],
  )

  const selectedMembership = React.useMemo(
    () => (selectedEnv ? membershipByEnvId.get(selectedEnv.id) ?? null : null),
    [selectedEnv, membershipByEnvId],
  )

  return (
    <>
      <InfoMessage collapseId={'random-identity-sample'}>
        {membersEnabled
          ? 'These are the Identities currently matching this Segment in the selected environment, based on the current Segment rules.'
          : 'This is a random sample of Identities who are either in or out of this Segment based on the current Segment rules.'}
      </InfoMessage>
      <div className='mt-2'>
        <FormGroup>
          <InputGroup
            title='Environment'
            className='col-4'
            component={
              <>
                <EnvironmentSelect
                  projectId={`${projectId}`}
                  value={environmentId}
                  onChange={(environmentId: string) => {
                    setEnvironmentId(environmentId)
                  }}
                  formatOptionLabel={renderEnvOption}
                />
                <div className='text-muted fs-small mt-2'>
                  Last synced:{' '}
                  {selectedMembership
                    ? moment(selectedMembership.last_synced_at).format(
                        'Do MMM YYYY HH:mm:ss',
                      )
                    : '—'}
                </div>
              </>
            }
          />
          {membersEnabled && segmentId && selectedEnv ? (
            <SegmentMembersList
              projectId={projectId}
              segmentId={segmentId}
              environmentId={selectedEnv.id}
              environmentApiKey={selectedEnv.api_key}
              count={selectedMembership?.count}
            />
          ) : (
            <PanelSearch
              renderSearchWithNoResults
              id='users-list'
              title='Segment Users'
              className='no-pad'
              isLoading={identitiesLoading}
              items={identities?.results}
              paging={identities}
              nextPage={() => {
                setPage({
                  number: page.number + 1,
                  pageType: 'NEXT',
                  pages: identities?.last_evaluated_key
                    ? (page.pages || []).concat([
                        identities?.last_evaluated_key,
                      ])
                    : undefined,
                })
              }}
              prevPage={() => {
                setPage({
                  number: page.number - 1,
                  pageType: 'PREVIOUS',
                  pages: page.pages
                    ? Utils.removeElementFromArray(
                        page.pages,
                        page.pages.length - 1,
                      )
                    : undefined,
                })
              }}
              goToPage={(newPage: number) => {
                setPage({
                  number: newPage,
                  pageType: undefined,
                  pages: undefined,
                })
              }}
              onRefresh={
                environmentId
                  ? () =>
                      getStore().dispatch(
                        identitySegmentService.util.invalidateTags([
                          'IdentitySegment',
                        ]),
                      )
                  : undefined
              }
              renderRow={({ id, identifier }, index) => (
                <UserRow
                  segmentName={name}
                  projectId={`${projectId}`}
                  index={index}
                  id={id}
                  identifier={identifier}
                />
              )}
              filterRow={() => true}
              search={searchInput}
              onChange={(e) => {
                setSearchInput(Utils.safeParseEventValue(e))
              }}
            />
          )}
        </FormGroup>
      </div>
    </>
  )
}

export default CreateSegmentUsersTabContent
