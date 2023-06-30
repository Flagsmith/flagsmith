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
import RemoveIcon from 'components/RemoveIcon'
import PanelSearch from 'components/PanelSearch'
import Button from 'components/base/forms/Button' // we need this to make JSX compile
import JSONReference from 'components/JSONReference' // we need this to make JSX compile
import Utils from 'common/utils/utils'

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
    openConfirm(
      "Delete User",
      <div>
        {'Are you sure you want to delete '}
        <strong>{identifier}</strong>
        {'?'}
      </div>,
      () => deleteIdentity({ environmentId, id, isEdge: Utils.getIsEdge() }),
    )
  }

  const newUser = () => {
    openModal('New Users', <CreateUserModal environmentId={environmentId} />)
  }

  return (
    <div className='app-container container'>
      <div>
        <div>
          <Row>
            <Flex>
              <div style={{ maxWidth: '700px' }}>
                <h4>Users</h4>
                <p>
                  View and manage features states for individual users. This
                  will override individual default feature settings for your
                  selected environment.{' '}
                  <Button
                    theme='text'
                    target='_blank'
                    href='https://docs.flagsmith.com/basic-features/managing-identities'
                  >
                    Learn more.
                  </Button>
                </p>
              </div>
            </Flex>
            {permission ? (
              <FormGroup className='float-right'>
                <Button
                  className='float-right'
                  data-test='show-create-feature-btn'
                  id='show-create-feature-btn'
                  onClick={newUser}
                >
                  Create Users
                </Button>
              </FormGroup>
            ) : (
              <Tooltip
                html
                title={
                  <Button
                    disabled
                    data-test='show-create-feature-btn'
                    id='show-create-feature-btn'
                    onClick={newUser}
                  >
                    Create Users
                  </Button>
                }
                place='right'
              >
                {Constants.environmentPermissions('Admin')}
              </Tooltip>
            )}
          </Row>
        </div>
        <FormGroup>
          <div>
            <FormGroup>
              <PanelSearch
                renderSearchWithNoResults
                renderFooter={() => (
                  <JSONReference
                    className='mx-2 mt-4'
                    title={'Users'}
                    json={identities?.results}
                  />
                )}
                id='users-list'
                title='Users'
                className='no-pad'
                isLoading={isLoading}
                filterLabel={Utils.getIsEdge() ? 'Starts with' : 'Contains'}
                icon='ion-md-person'
                items={identities?.results}
                paging={identities}
                showExactFilter
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
                renderRow={(
                  { id, identifier, identity_uuid }: Identity,
                  index: number,
                ) =>
                  permission ? (
                    <Row
                      space
                      className='list-item clickable'
                      key={id}
                      data-test={`user-item-${index}`}
                    >
                      <Flex>
                        <Link
                          to={`/project/${
                            props.match.params.projectId
                          }/environment/${
                            props.match.params.environmentId
                          }/users/${encodeURIComponent(identifier)}/${id}`}
                        >
                          <Button theme='text'>
                            {identifier}
                            <span className='ion-ios-arrow-forward ml-3' />
                          </Button>
                        </Link>
                      </Flex>
                      <Column>
                        <button
                          id='remove-feature'
                          className='btn btn--with-icon'
                          type='button'
                          onClick={() => {
                            if (id) {
                              removeIdentity(id, identifier)
                            } else if (identity_uuid) {
                              removeIdentity(identity_uuid, identifier)
                            }
                          }}
                        >
                          <RemoveIcon />
                        </button>
                      </Column>
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
                  <div>
                    You have no users in your project
                    {search ? (
                      <span>
                        {' '}
                        for <strong>"{search}"</strong>
                      </span>
                    ) : (
                      ''
                    )}
                    .
                  </div>
                }
                filterRow={() => true}
                search={searchInput}
                onChange={(e: InputEvent) => {
                  setSearchInput(Utils.safeParseEventValue(e))
                }}
              />
            </FormGroup>
            <FormGroup>
              <p className='faint mt-4'>
                Users are created for your environment automatically when
                calling identify/get flags from any of the SDKs.
                <br />
                We've created <strong>user_123456</strong> for you so you always
                have an example user to test with on your environments.
              </p>
              <div className='row'>
                <div className='col-md-12'>
                  <CodeHelp
                    showInitially
                    title='Creating users and getting their feature settings'
                    snippets={Constants.codeHelp.CREATE_USER(
                      props.match.params.environmentId,
                      identities?.results?.[0]?.identifier,
                    )}
                  />
                </div>
              </div>
            </FormGroup>
          </div>
        </FormGroup>
      </div>
    </div>
  )
}

export default ConfigProvider(UsersPage)
