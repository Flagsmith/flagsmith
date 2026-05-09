import React, { FC } from 'react'
import moment from 'moment'
import EnvironmentSelect from 'components/EnvironmentSelect'
import PanelSearch from 'components/PanelSearch'
import InfoMessage from 'components/InfoMessage'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import { Environment, Res, SegmentMembership } from 'common/types/responses'
import Icon from 'components/icons/Icon'
import {
  identitySegmentService,
  useGetIdentitySegmentsQuery,
} from 'common/services/useIdentitySegment'
import { getStore } from 'common/store'
import ProjectStore from 'common/stores/project-store'
import { SegmentMembershipEnvBadge } from 'components/segments/SegmentMembershipBadge'

interface CreateSegmentUsersTabContentProps {
  projectId: string | number
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
}

type EnvOption = {
  value: string
  label: string
  environment: Environment
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
  memberships,
  name,
  page,
  projectId,
  searchInput,
  setEnvironmentId,
  setPage,
  setSearchInput,
}) => {
  const membershipByEnvId = React.useMemo(() => {
    const map = new Map<number, SegmentMembership>()
    ;(memberships ?? []).forEach((m) => map.set(m.environment, m))
    return map
  }, [memberships])

  const renderEnvOption = (data: unknown) => {
    const { environment, label } = data as Partial<EnvOption>
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

  const selectedMembership = React.useMemo(() => {
    if (!environmentId) return null
    const envs = (ProjectStore.getEnvs() as Environment[] | null) || []
    const env = envs.find((e) => e.api_key === environmentId)
    return env ? membershipByEnvId.get(env.id) ?? null : null
  }, [environmentId, membershipByEnvId])

  return (
    <>
      <InfoMessage collapseId={'random-identity-sample'}>
        This is a random sample of Identities who are either in or out of this
        Segment based on the current Segment rules.
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
                  ? (page.pages || []).concat([identities?.last_evaluated_key])
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
        </FormGroup>
      </div>
    </>
  )
}

export default CreateSegmentUsersTabContent
