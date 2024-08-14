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
import Input from './base/forms/Input'
import Project from 'common/project'
export type SamlTabType = {
  organisationId: number
}

const copyAcsUrl = async (configurationName: string) => {
  await navigator.clipboard.writeText(
    `${Project.flagsmithClientAPI}auth/saml/${configurationName}/response/`,
  )
  toast('Copied to clipboard')
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
    <div className='mt-3'>
      <PageTitle
        title={'SAML Configurations'}
        cta={
          <Button
            className='text-right'
            onClick={() => {
              openCreateSAML('Create SAML configuration', organisationId)
            }}
          >
            {'Create a SAML configuration'}
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
              <Flex className='table-column'>
                <div className='font-weight-medium'>Configuration name</div>
              </Flex>
              <div className='table-column' style={{ width: '400px' }}>
                Assertion Consumer Service (ACS) URL
              </div>
              <div className='table-column' style={{ width: '150px' }}>
                Allow IdP-initiated
              </div>
              <div style={{ width: 90 }} className='table-column'>
                Action
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
              <div
                onClick={(e) => e.stopPropagation()}
                className='table-column flex flex-row gap-2'
                style={{ width: '400px' }}
              >
                <div className='flex-1'>
                  <Input
                    className='full-width'
                    value={`${Project.flagsmithClientAPI}auth/saml/${samlConf.name}/response/`}
                    readOnly
                  />
                </div>
                <Button
                  onClick={() => {
                    copyAcsUrl(samlConf.name)
                  }}
                  className='me-2 btn-with-icon'
                >
                  <Icon name='copy' width={20} fill='#656D7B' />
                </Button>
              </div>
              <div
                className='table-column d-flex gap-4 align-items-center'
                style={{ width: '150px' }}
              >
                <Switch checked={samlConf.allow_idp_initiated} />
              </div>
              <div className='table-column' style={{ width: 90 }}>
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
    </div>
  )
}

export default SamlTab
