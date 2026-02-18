import React, { FC } from 'react'
import Button from './base/forms/Button'
import Icon from './Icon'
import PanelSearch from './PanelSearch'
import PageTitle from './PageTitle'
import {
  useDeleteOidcConfigurationMutation,
  useGetOidcConfigurationsQuery,
} from 'common/services/useOidcConfiguration'
import CreateOIDC from './modals/CreateOIDC'
import Switch from './Switch'
import PlanBasedBanner from './PlanBasedAccess'

export type OidcTabType = {
  organisationId: number
}

const OidcTab: FC<OidcTabType> = ({ organisationId }) => {
  const { data } = useGetOidcConfigurationsQuery({
    organisation_id: organisationId,
  })
  const [deleteOidcConfiguration] = useDeleteOidcConfigurationMutation()

  const openCreateOIDC = (
    title: string,
    organisationId: number,
    name?: string,
  ) => {
    openModal(
      title,
      <CreateOIDC organisationId={organisationId} oidcName={name || ''} />,
      'p-0 side-modal',
    )
  }

  return (
    <PlanBasedBanner feature='OIDC' theme='page'>
      <div className='mt-4 mb-4'>
        <PageTitle
          title={'OIDC Configurations'}
          cta={
            <Button
              className='text-right'
              onClick={() => {
                openCreateOIDC('Create OIDC configuration', organisationId)
              }}
            >
              {'Create an OIDC configuration'}
            </Button>
          }
        />

        <FormGroup>
          <PanelSearch
            className='no-pad overflow-visible'
            id='oidc-list'
            renderSearchWithNoResults
            itemHeight={65}
            isLoading={false}
            filterRow={(oidcConf, search: string) =>
              oidcConf.name.toLowerCase().indexOf(search) > -1
            }
            header={
              <Row className='table-header'>
                <Flex className='table-column'>
                  <div className='font-weight-medium'>Configuration name</div>
                </Flex>
                <div
                  className='table-column d-none d-md-block'
                  style={{ width: '150px' }}
                >
                  Provider URL
                </div>
                <div
                  className='table-column d-none d-md-block'
                  style={{ width: '150px' }}
                >
                  Allow IdP-initiated
                </div>
                <div style={{ width: 90 }} className='table-column'>
                  Action
                </div>
              </Row>
            }
            items={data?.results || []}
            renderRow={(oidcConf) => (
              <Row
                onClick={() => {
                  openCreateOIDC(
                    'Update OIDC configuration',
                    organisationId,
                    oidcConf.name,
                  )
                }}
                space
                className='list-item py-2 py-md-0 clickable cursor-pointer'
                key={oidcConf.name}
              >
                <Flex className='table-column px-3'>
                  <div className='font-weight-medium mb-1'>{oidcConf.name}</div>
                </Flex>
                <div
                  className='table-column d-none d-md-flex gap-4 align-items-center'
                  style={{ width: '150px' }}
                >
                  <span className='text-truncate fs-small text-muted'>
                    {oidcConf.provider_url}
                  </span>
                </div>
                <div
                  className='table-column d-none d-md-flex gap-4 align-items-center'
                  style={{ width: '150px' }}
                >
                  <Switch checked={oidcConf.allow_idp_initiated} />
                </div>
                <div className='table-column' style={{ width: 90 }}>
                  <Button
                    id='delete-oidc'
                    type='button'
                    onClick={(e) => {
                      openModal(
                        'Delete OIDC configuration',
                        <div>
                          <div>
                            Are you sure you want to delete the OIDC
                            configuration?
                          </div>
                          <div className='text-right'>
                            <Button
                              className='mr-2'
                              onClick={() => {
                                closeModal()
                              }}
                            >
                              Cancel
                            </Button>
                            <Button
                              theme='danger'
                              onClick={() => {
                                deleteOidcConfiguration({
                                  name: oidcConf.name,
                                }).then(() => {
                                  toast('OIDC configuration deleted')
                                  closeModal()
                                })
                              }}
                            >
                              Delete
                            </Button>
                          </div>
                        </div>,
                      )
                      e.stopPropagation()
                      e.preventDefault()
                    }}
                    className='btn btn-with-icon'
                  >
                    <Icon name='trash-2' width={20} fill='#656D7B' />
                  </Button>
                </div>
              </Row>
            )}
          />
        </FormGroup>
      </div>
    </PlanBasedBanner>
  )
}

export default OidcTab
