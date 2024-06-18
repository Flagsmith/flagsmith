import React, { FC } from 'react'

import {
  useDeleteSamlAttributeMappingMutation,
  useGetSamlAttributeMappingQuery,
} from 'common/services/useSamlAttributeMapping'
import PanelSearch from './PanelSearch'
import Button from './base/forms/Button'
import Icon from './Icon'
import { SAMLAttributeMapping } from 'common/types/responses'

type SAMLAttributeMappingTableType = {
  samlConfigurationId: number
}
const SAMLAttributeMappingTable: FC<SAMLAttributeMappingTableType> = ({
  samlConfigurationId,
}) => {
  const { data } = useGetSamlAttributeMappingQuery({
    saml_configuration_id: samlConfigurationId,
  })

  const [deleteSamlAttribute] = useDeleteSamlAttributeMappingMutation()

  return (
    <div>
      <PanelSearch
        className='no-pad overflow-visible'
        id='features-list'
        renderSearchWithNoResults
        itemHeight={65}
        isLoading={false}
        header={
          <Row className='table-header'>
            <Flex className='table-column px-3'>
              <div className='font-weight-medium'>SAML Attribute Name</div>
            </Flex>
            <div className='table-column' style={{ width: '205px' }}>
              IDP Attribute Name
            </div>
          </Row>
        }
        items={data?.results || []}
        renderRow={(attribute: SAMLAttributeMapping) => (
          <Row
            space
            className='list-item clickable cursor-pointer'
            key={attribute.django_attribute_name}
          >
            <Flex className='table-column px-3'>
              <div className='font-weight-medium mb-1'>
                {attribute.django_attribute_name}
              </div>
            </Flex>
            <div className='table-column' style={{ width: '95px' }}>
              {attribute.idp_attribute_name}
            </div>
            <div className='table-column'>
              <Button
                id='delete-attribute'
                data-test='delete-attribute'
                type='button'
                onClick={(e) => {
                  openModal2(
                    'Delete SAML attribute',
                    <div>
                      <div>
                        Are you sure you want to delete this SAML attribute?
                      </div>
                      <div className='text-right'>
                        <Button
                          className='mr-2'
                          onClick={() => {
                            closeModal2()
                          }}
                        >
                          Cancel
                        </Button>
                        <Button
                          theme='danger'
                          onClick={() => {
                            deleteSamlAttribute({
                              attribute_id: attribute.id,
                            }).then(() => {
                              toast('SAML attribute deleted')
                              closeModal2()
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
    </div>
  )
}
export default SAMLAttributeMappingTable
