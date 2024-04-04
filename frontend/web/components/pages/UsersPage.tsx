import React, { FC, useState } from 'react'
import { RouterChildContext } from 'react-router'
import { Link } from 'react-router-dom'
import { useHasPermission } from 'common/providers/Permission'
import ConfigProvider from 'common/providers/ConfigProvider'

import Constants from 'common/constants'
import {
  useDeleteIdentityMutation,
  useGetIdentitiesQuery,
} from 'common/services/useIdentity'
import useSearchThrottle from 'common/useSearchThrottle'
import { Req } from 'common/types/requests'
import { Identity } from 'common/types/responses'
import CreateUserModal from 'components/modals/CreateUser'
import PanelSearch from 'components/PanelSearch'
import Button from 'components/base/forms/Button' // we need this to make JSX compile
import JSONReference from 'components/JSONReference' // we need this to make JSX compile
import Utils from 'common/utils/utils'
import Icon from 'components/Icon'
import PageTitle from 'components/PageTitle'
import Format from 'common/utils/format'
import IdentifierString from 'components/IdentifierString'

const CodeHelp = require('../CodeHelp')

type UsersPageType = {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}
const UsersPage: FC<UsersPageType> = (props) => {
  const [page, setPage] = useState<{
    number: number
    pageType: Req['getIdentities']['pageType']
    pages: Req['getIdentities']['pages']
  }>({ number: 1, pageType: undefined, pages: undefined })

  const { search, searchInput, setSearchInput } = useSearchThrottle(
    Utils.fromParam().search,
    () => {
      setPage({
        number: 1,
        pageType: undefined,
        pages: undefined,
      })
    },
  )
  const [deleteIdentity] = useDeleteIdentityMutation({})
  const isEdge = Utils.getIsEdge()

  const { data: identities, isLoading } = useGetIdentitiesQuery({
    environmentId: props.match.params.environmentId,
    isEdge,
    page: page.number,
    pageType: page.pageType,
    page_size: 10,
    pages: page.pages,
    search,
  })

  const { environmentId } = props.match.params

  const { permission } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: Utils.getViewIdentitiesPermission(),
  })

  const removeIdentity = (id: string, identifier: string) => {
    openConfirm({
      body: (
        <div>
          {'Are you sure you want to delete '}
          <strong>{identifier}</strong>
          {'? Identities can be re-added here or via one of our SDKs.'}
        </div>
      ),
      destructive: true,
      onYes: () =>
        deleteIdentity({ environmentId, id, isEdge: Utils.getIsEdge() }),
      title: 'Delete User',
      yesText: 'Confirm',
    })
  }

  const newUser = () => {
    openModal(
      'New Identities',
      <CreateUserModal environmentId={environmentId} />,
      'side-modal',
    )
  }

  return (
    <div className='app-container container'>
      <PageTitle
        cta={
          <>
            {permission ? (
              <FormGroup className='float-right'>
                <Button
                  className='float-right'
                  data-test='show-create-feature-btn'
                  id='show-create-feature-btn'
                  onClick={newUser}
                >
                  Create Identities
                </Button>
              </FormGroup>
            ) : (
              <Tooltip
                title={
                  <Button
                    disabled
                    data-test='show-create-feature-btn'
                    id='show-create-feature-btn'
                    onClick={newUser}
                  >
                    Create Identities
                  </Button>
                }
                place='right'
              >
                {Constants.environmentPermissions('Admin')}
              </Tooltip>
            )}
          </>
        }
        title={'Identities'}
      >
        View and manage features states for individual identities. This will
        override individual default feature settings for your selected
        environment.{' '}
        <Button
          theme='text'
          target='_blank'
          href='https://docs.flagsmith.com/basic-features/managing-identities'
          className='fw-normal'
        >
          Learn more.
        </Button>
      </PageTitle>
      <div>
        <FormGroup>
          <PanelSearch
            renderSearchWithNoResults
            renderFooter={() => (
              <JSONReference
                className='mx-2 mt-4'
                title={'Identites'}
                json={identities?.results}
              />
            )}
            id='users-list'
            title='Identities'
            className='no-pad'
            isLoading={isLoading}
            filterLabel={Utils.getIsEdge() ? 'Starts with' : 'Contains'}
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
            renderRow={(
              { id, identifier, identity_uuid }: Identity,
              index: number,
            ) =>
              permission ? (
                <Row
                  space
                  className='list-item clickable list-item-sm'
                  key={id}
                  data-test={`user-item-${index}`}
                >
                  <Link
                    to={`/project/${props.match.params.projectId}/environment/${
                      props.match.params.environmentId
                    }/users/${encodeURIComponent(identifier)}/${id}`}
                    className='flex-row flex flex-1 table-column'
                  >
                    <div className='font-weight-medium'>
                      <IdentifierString value={identifier} />
                    </div>
                    <Icon
                      name='chevron-right'
                      width={22}
                      fill={
                        Utils.getFlagsmithHasFeature('dark_mode')
                          ? '#FFF'
                          : '#656D7B'
                      }
                    />
                  </Link>
                  <div className='table-column'>
                    <Button
                      id='remove-feature'
                      className='btn btn-with-icon'
                      type='button'
                      onClick={() => {
                        if (id) {
                          removeIdentity(id, identifier)
                        } else if (identity_uuid) {
                          removeIdentity(identity_uuid, identifier)
                        }
                      }}
                    >
                      <Icon name='trash-2' width={20} fill='#656D7B' />
                    </Button>
                  </div>
                </Row>
              ) : (
                <Row
                  space
                  className='list-item'
                  key={id}
                  data-test={`user-item-${index}`}
                >
                  {identifier}
                </Row>
              )
            }
            renderNoResults={
              <Row className='list-item p-3'>
                You have no identities in this environment
                {search ? (
                  <span>
                    {' '}
                    for <strong>"{search}"</strong>
                  </span>
                ) : (
                  ''
                )}
                .
              </Row>
            }
            filterRow={() => true}
            search={searchInput}
            onChange={(e: InputEvent) => {
              setSearchInput(Utils.safeParseEventValue(e))
            }}
          />
        </FormGroup>
        <FormGroup>
          <p className='text-muted col-md-8 fs-small lh-sm mt-4'>
            Identities are created for your environment automatically when
            calling identify/get flags from any of the SDKs. We've created{' '}
            <strong>user_123456</strong> for you so you always have an example
            identity to test with on your environments.
          </p>
          <div className='row'>
            <div className='col-md-12'>
              <CodeHelp
                showInitially
                title='Creating identities and getting their feature settings'
                snippets={Constants.codeHelp.CREATE_USER(
                  props.match.params.environmentId,
                  identities?.results?.[0]?.identifier,
                )}
              />
            </div>
          </div>
        </FormGroup>
      </div>
    </div>
  )
}

export default ConfigProvider(UsersPage)
