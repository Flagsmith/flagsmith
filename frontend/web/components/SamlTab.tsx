import React, { FC, useState } from 'react'
import Switch from './Switch'
import InputGroup from './base/forms/InputGroup'
import Button from './base/forms/Button'
import ValueEditor from './ValueEditor'
import Utils from 'common/utils/utils'
import {
  useCreateSamlConfigurationMutation,
  useUpdateSamlConfigurationMutation,
  useDeleteSamlConfigurationMutation,
  useGetSamlConfigurationQuery,
} from 'common/services/useSamlConfiguration'
import { SAMLConfiguration } from 'common/types/responses'
import Icon from './Icon'

export type SamlTabType = {
  organisationId: number
}
const SamlTab: FC<SamlTabType> = ({ organisationId }) => {
  const [name, setName] = useState<string>('')
  const [frontendUrl, setFrontendUrl] = useState<string>(window.location.origin)
  const [metadataXml, setMetadataXml] = useState<string>('')
  const [allowIdpInitiated, setAllowIdpInitiated] = useState<boolean>(false)
  const [createSamlConfiguration] = useCreateSamlConfigurationMutation()
  const [editSamlCOnfiguration] = useUpdateSamlConfigurationMutation()
  const [deleteSamlConfiguration] = useDeleteSamlConfigurationMutation()
  const { data } = useGetSamlConfigurationQuery({ name: name }, { skip: !name })

  return (
    <div className='col-md-8 mt-3'>
      <h5 className='mb-5'>SAML Configuration</h5>
      <InputGroup
        className='mt-2'
        title='Name*'
        data-test='saml-name'
        value={name}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          setName(Utils.safeParseEventValue(event))
        }}
        inputProps={{
          className: 'full-width',
        }}
        type='text'
        name='Name*'
      />
      <InputGroup
        className='mt-2 mb-4'
        title='Frontend URL*'
        data-test='frontend-url'
        value={frontendUrl}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          setFrontendUrl(Utils.safeParseEventValue(event))
        }}
        inputProps={{
          className: 'full-width',
          name: 'groupName',
        }}
        type='text'
        name='Frontend URL*'
      />
      <InputGroup
        className='mt-2 mb-4'
        title='Allow idp initiated'
        component={
          <Switch
            checked={allowIdpInitiated}
            onChange={() => {
              setAllowIdpInitiated(!allowIdpInitiated)
            }}
          />
        }
      />
      <FormGroup className='mb-4'>
        <InputGroup
          component={
            <ValueEditor
              data-test='featureValue'
              name='featureValue'
              className='full-width'
              value={metadataXml}
              onChange={setMetadataXml}
              placeholder="e.g. '<xml>time<xml>' "
            />
          }
          title={'IPD Metadata XML'}
        />
      </FormGroup>
      <form className='text-right'>
        <div className='text-right mt-2'>
          <Button
            type='submit'
            disabled={!name || !frontendUrl}
            onClick={() => {
              const body = {
                frontend_url: frontendUrl,
                name: name,
                organisation: organisationId,
              } as SAMLConfiguration
              if (metadataXml) {
                body.idp_metadata_xml = metadataXml
              }
              if (allowIdpInitiated) {
                body.allow_idp_initiated = allowIdpInitiated
              }
              if (data) {
                editSamlCOnfiguration(body).then((res) => {
                  if (res.data) {
                    setName(res.data.organisation)
                    setFrontendUrl(res.data.name)
                    setMetadataXml(res.data.idp_metadata_xml)
                    setAllowIdpInitiated(res.data.allow_idp_initiated)
                  }
                })
              } else {
                createSamlConfiguration(body).then((res) => {
                  if (res.data) {
                    setName(res.data.organisation)
                    setFrontendUrl(res.data.name)
                    setMetadataXml(res.data.idp_metadata_xml)
                    setAllowIdpInitiated(res.data.allow_idp_initiated)
                  }
                })
              }
            }}
          >
            {data ? 'Edit Configuration' : 'Create Configuration'}
          </Button>
        </div>
      </form>
      <hr className='py-0 my-4' />
      {data && (
        <FormGroup className='mt-4 col-md-6'>
          <Row space>
            <div className='col-md-7'>
              <h5 className='mn-2'>Delete SAML configuration</h5>
              <p className='fs-small lh-sm'>
                This SAML configuration will be permanently deleted.s
              </p>
            </div>
            <Button
              id='delete-saml-configuration'
              onClick={() => {
                deleteSamlConfiguration({ name: name }).then((res) => {
                  if (res.data) {
                    setName('')
                    setMetadataXml('')
                    setAllowIdpInitiated(false)
                  }
                })
              }}
              className='btn-with-icon btn-remove'
            >
              <Icon name='trash-2' width={20} fill='#EF4D56' />
            </Button>
          </Row>
        </FormGroup>
      )}
    </div>
  )
}

export default SamlTab
