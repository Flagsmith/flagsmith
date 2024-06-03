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

export type SamlTabType = {
  organisationId: number
}
const SamlTab: FC<SamlTabType> = ({ organisationId }) => {
  const { data } = useGetSamlConfigurationsQuery({
    organisation_id: organisationId,
  })
  const [deleteSamlConfiguration] = useDeleteSamlConfigurationMutation()
  const openCreateSAML = (organisationId: number, name?: string) => {
    openModal(
      'New SAML configuration',
      <CreateSAML organisationId={organisationId} samlName={name || ''} />,
      'p-0 side-modal',
    )
  }

  return (
    <div className='mt-3'>
      <PageTitle
        title={'SAML Configuration'}
        cta={
          <Button
            className='text-right'
            onClick={() => {
              openCreateSAML(organisationId)
            }}
          >
            {'Create a SAML Configuration'}
          </Button>
        }
      ></PageTitle>

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
              <Flex className='table-column'>
                <div className='font-weight-medium mb-1'>SAML Name</div>
              </Flex>
              <div className='table-column'>Allow IDP Initiated</div>
            </Row>
          }
          items={data}
          renderRow={(samlConf: SAMLConfiguration) => (
            <Row
              onClick={() => {
                openCreateSAML(organisationId, samlConf.name)
              }}
              space
              className='list-item clickable cursor-pointer'
              key={samlConf.name}
            >
              <Flex className='table-column px-3'>
                <div className='font-weight-medium mb-1'>{samlConf.name}</div>
              </Flex>
              <div className='table-column'>
                <Switch checked={samlConf.allow_idp_initiated} />
              </div>
              <div className='table-column'>
                <Button
                  id='delete-invite'
                  type='button'
                  onClick={(e) => {
                    e.stopPropagation()
                    e.preventDefault()
                    deleteSamlConfiguration({ name: samlConf.name }).then(
                      () => {
                        toast('SAML configuration deleted')
                        closeModal()
                      },
                    )
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
  )
}

export default SamlTab
