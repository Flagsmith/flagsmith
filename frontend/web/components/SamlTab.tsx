import React, { FC } from 'react'
import Button from './base/forms/Button'

import Icon from './Icon'
import PanelSearch from './PanelSearch'
import PageTitle from './PageTitle'

import {
  useDeleteSamlConfigurationMutation,
  useGetSamlConfigurationsQuery,
} from 'common/services/useSamlConfiguration'
import CreateSAML from './modals/CreateSAML'
import Switch from './Switch'
import { SAMLConfiguration } from 'common/types/responses'
import PlanBasedBanner from './PlanBasedAccess'

export type SamlTabType = {
  organisationId: number
}
const SamlTab: FC<SamlTabType> = ({ organisationId }) => {
  const { data } = useGetSamlConfigurationsQuery({
    organisation_id: organisationId,
  })
  const [deleteSamlConfiguration] = useDeleteSamlConfigurationMutation()
  const openCreateSAML = (
    title: string,
    organisationId: number,
    name?: string,
  ) => {
    openModal(
      title,
      <CreateSAML organisationId={organisationId} samlName={name || ''} />,
      'p-0 side-modal',
    )
  }

  return (
    <PlanBasedBanner feature={'SAML'} theme={'page'} className='mt-3'>
      <PageTitle
        title={'SAML Configuration'}
        cta={
          <Button
            className='text-right'
            onClick={() => {
              openCreateSAML('Create SAML configuration', organisationId)
            }}
          >
            {'Create a SAML Configuration'}
          </Button>
        }
      />

      <FormGroup className='mb-4'>
        <PanelSearch
          className='no-pad overflow-visible'
          id='features-list'
          renderSearchWithNoResults
          itemHeight={65}
          isLoading={false}
          filterRow={(samlConf: SAMLConfiguration, search: string) =>
            samlConf.name.toLowerCase().indexOf(search) > -1
          }
          header={
            <Row className='table-header'>
              <Flex className='table-column px-3'>
                <div className='font-weight-medium'>SAML Name</div>
              </Flex>
              <div className='table-column' style={{ width: '205px' }}>
                Allow IDP Initiated
              </div>
            </Row>
          }
          items={data?.results || []}
          renderRow={(samlConf: SAMLConfiguration) => (
            <Row
              onClick={() => {
                openCreateSAML(
                  'Update SAML configuration',
                  organisationId,
                  samlConf.name,
                )
              }}
              space
              className='list-item clickable cursor-pointer'
              key={samlConf.name}
            >
              <Flex className='table-column px-3'>
                <div className='font-weight-medium mb-1'>{samlConf.name}</div>
              </Flex>
              <div className='table-column' style={{ width: '95px' }}>
                <Switch checked={samlConf.allow_idp_initiated} />
              </div>
              <div className='table-column'>
                <Button
                  id='delete-invite'
                  type='button'
                  onClick={(e) => {
                    openModal(
                      'Delete SAML configuration',
                      <div>
                        <div>
                          Are you sure you want to delete the SAML
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
                              deleteSamlConfiguration({
                                name: samlConf.name,
                              }).then(() => {
                                toast('SAML configuration deleted')
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
    </PlanBasedBanner>
  )
}

export default SamlTab
