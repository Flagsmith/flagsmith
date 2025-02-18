import React from 'react'
import EnvironmentSelect from 'components/EnvironmentSelect'
import IdentitySegmentsProvider from 'common/providers/IdentitySegmentsProvider'
import PanelSearch from 'components/PanelSearch'
import InfoMessage from 'components/InfoMessage'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import { Res, Segment } from 'common/types/responses'
import Icon from 'components/Icon'
import AppActions from 'common/dispatcher/app-actions'
import {
  identitySegmentService,
  useGetIdentitySegmentsQuery,
} from 'common/services/useIdentitySegment'

interface CreateSegmentUsersTabContentProps {
  projectId: string | number
  environmentId: string
  setEnvironmentId: (environmentId: string) => void
  identitiesLoading: boolean
  identities: Res['identities']
  page: any
  setPage: (page: any) => void
  name: string
  searchInput: string
  setSearchInput: (input: string) => void
}

import { FC } from 'react'
import { getStore } from 'common/store'

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
  name,
  page,
  projectId,
  searchInput,
  setEnvironmentId,
  setPage,
  setSearchInput,
}) => {
  return (
    <div className='my-4'>
      <InfoMessage collapseId={'random-identity-sample'}>
        This is a random sample of Identities who are either in or out of this
        Segment based on the current Segment rules.
      </InfoMessage>
      <div className='mt-2'>
        <FormGroup>
          <InputGroup
            title='Environment'
            component={
              <EnvironmentSelect
                projectId={`${projectId}`}
                value={environmentId}
                onChange={(environmentId: string) => {
                  setEnvironmentId(environmentId)
                }}
              />
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
            showExactFilter
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
            renderRow={(
              { id, identifier }: { id: string; identifier: string },
              index: number,
            ) => (
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
            onChange={(e: InputEvent) => {
              setSearchInput(Utils.safeParseEventValue(e))
            }}
          />
        </FormGroup>
      </div>
    </div>
  )
}

export default CreateSegmentUsersTabContent
