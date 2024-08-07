import React, { FC, useEffect, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import Switch from 'components/Switch'
import ValueEditor from 'components/ValueEditor'
import {
  useCreateSamlConfigurationMutation,
  useUpdateSamlConfigurationMutation,
  useGetSamlConfigurationQuery,
  getSamlConfigurationMetadata,
} from 'common/services/useSamlConfiguration'
import { useCreateSamlAttributeMappingMutation } from 'common/services/useSamlAttributeMapping'
import Button from 'components/base/forms/Button'
import { Req } from 'common/types/requests'
import ErrorMessage from 'components/ErrorMessage'
import { getStore } from 'common/store'
import XMLUpload from 'components/XMLUpload'
import { IonIcon } from '@ionic/react'
import { cloudDownloadOutline } from 'ionicons/icons'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import { AttributeName } from 'common/types/responses'
import SAMLAttributeMappingTable from 'components/SAMLAttributeMappingTable'

type CreateSAML = {
  organisationId: number
  samlName?: string
}

type samlAttributeType = { id: number; label: string; value: AttributeName }
type samlAttributesType = samlAttributeType[]

const CreateSAML: FC<CreateSAML> = ({ organisationId, samlName }) => {
  const [previousName, setPreviousName] = useState<string>(samlName || '')
  const [name, setName] = useState<string>(samlName || '')
  const [frontendUrl, setFrontendUrl] = useState<string>(window.location.origin)
  const [metadataXml, setMetadataXml] = useState<string>('')
  const [allowIdpInitiated, setAllowIdpInitiated] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [file, setFile] = useState<File | null>(null)
  const [isEdit, setIsEdit] = useState<boolean>(!!samlName || false)
  const [
    createSamlConfiguration,
    { error: createError, isError: hasCreateError },
  ] = useCreateSamlConfigurationMutation()
  const [
    editSamlConfiguration,
    { error: updateError, isError: hasUpdateError },
  ] = useUpdateSamlConfigurationMutation()
  const { data, isSuccess } = useGetSamlConfigurationQuery(
    { name: samlName! },
    { skip: !samlName },
  )

  useEffect(() => {
    if (isSuccess && data) {
      setPreviousName(data.name)
    }
  }, [data, isSuccess])

  const samlAttributes: samlAttributesType = [
    { id: 1, label: 'Email', value: 'email' },
    { id: 2, label: 'First name', value: 'first_name' },
    { id: 3, label: 'Last name', value: 'last_name' },
    { id: 4, label: 'Groups', value: 'groups' },
  ]
  const validateName = (name: string) => {
    const regularExpresion = /^$|^[a-zA-Z0-9_+-]+$/
    return regularExpresion.test(name)
  }

  const convertToXmlFile = (fileName: string, data: string) => {
    const blob = new Blob([data], { type: 'application/xml' })
    const link = document.createElement('a')
    link.download = `${fileName}.xml`
    link.href = window.URL.createObjectURL(blob)
    link.click()
  }

  const downloadServiceProvider = () => {
    setIsLoading(true)
    getSamlConfigurationMetadata(getStore(), { name: previousName })
      .then((res) => {
        if (res.error) {
          convertToXmlFile(previousName, res.error.data)
        }
      })
      .finally(() => {
        setIsLoading(false)
      })
  }

  const downloadIDPMetadata = () => {
    const name = data?.name || samlName
    convertToXmlFile(`IDP metadata ${name!}`, data?.idp_metadata_xml || '')
  }

  const Tab1 = (
    <div className='create-feature-tab px-3 mt-3'>
      <InputGroup
        className='mt-2'
        title='Name*'
        data-test='saml-name'
        tooltip='A short name for the organization, used as the input when clicking "Single Sign-on" at login, should only consist of alphanumeric characters, plus (+), underscore (_), and hyphen (-).'
        tooltipPlace='right'
        value={name}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          const newName = Utils.safeParseEventValue(event).replace(/ /g, '_')
          if (validateName(newName)) {
            setName(newName)
          }
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
        tooltip='The base URL of the Flagsmith dashboard'
        tooltipPlace='right'
        value={data?.frontend_url || frontendUrl}
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
        title='Allow IDP initiated'
        tooltip='Determines whether logins can be initiated from the IDP'
        tooltipPlace='right'
        component={
          <Switch
            checked={allowIdpInitiated || data?.allow_idp_initiated}
            onChange={() => {
              setAllowIdpInitiated(!allowIdpInitiated)
            }}
          />
        }
      />
      <FormGroup className='mb-1'>
        <div className='mt-2 p-0'>
          <Row>
            <label className='form-label'>IDP Metadata XML</label>
            {data?.idp_metadata_xml && (
              <div className='ml-2 clickable' onClick={downloadIDPMetadata}>
                <Tooltip
                  title={
                    <IonIcon
                      className='text-primary'
                      icon={cloudDownloadOutline}
                      style={{ fontSize: '18px' }}
                    />
                  }
                  place='right'
                >
                  Download IDP Metadata
                </Tooltip>
              </div>
            )}
          </Row>
          {(!samlName ||
            (data &&
              ((data.name && !data.idp_metadata_xml) ||
                data.idp_metadata_xml))) && (
            <ValueEditor
              data-test='featureValue'
              name='featureValue'
              className='full-width'
              value={metadataXml || data?.idp_metadata_xml}
              onChange={setMetadataXml}
              placeholder="e.g. '<xml>time<xml>' "
              onlyOneLang
              language='xml'
            />
          )}
          <Row className='or-divider my-1'>
            <Flex className='or-divider__line' />
            Or
            <Flex className='or-divider__line' />
          </Row>
          <XMLUpload
            value={file}
            onChange={(file, data) => {
              setFile(file)
              setMetadataXml(data as string)
            }}
          />
        </div>
      </FormGroup>
      {(!!hasCreateError || !!hasUpdateError) && (
        <div className='mt-2'>
          <ErrorMessage error={createError || updateError} />
        </div>
      )}
      <div className='text-right py-2'>
        {isEdit && (
          <Button
            disabled={isLoading}
            onClick={downloadServiceProvider}
            className='mr-2'
          >
            {isLoading ? 'Downloading' : 'Download Service Provider Metadata'}
          </Button>
        )}
        <Button
          type='submit'
          disabled={!name || !frontendUrl}
          onClick={() => {
            const body = {
              frontend_url: frontendUrl,
              name: name,
              organisation: organisationId,
            } as Req['updateSamlConfiguration']['body']
            if (metadataXml) {
              body.idp_metadata_xml = metadataXml
            }
            if (allowIdpInitiated) {
              body.allow_idp_initiated = allowIdpInitiated
            }
            if (isEdit) {
              const samlNameConfiguration = previousName
              editSamlConfiguration({
                body: { ...body },
                name: samlNameConfiguration,
              }).then((res) => {
                if (res.data) {
                  setName(res.data.name)
                  setFrontendUrl(res.data.frontend_url)
                  setMetadataXml(res.data.idp_metadata_xml)
                  setAllowIdpInitiated(res.data.allow_idp_initiated)
                  setPreviousName(res.data.name)
                  toast('SAML configuration updated!')
                }
              })
            } else {
              createSamlConfiguration(body).then((res) => {
                if (res.data) {
                  setName(res.data.name)
                  setFrontendUrl(res.data.frontend_url)
                  setMetadataXml(res.data.idp_metadata_xml)
                  setAllowIdpInitiated(res.data.allow_idp_initiated)
                  toast('SAML configuration Created!')
                  setIsEdit(true)
                  setPreviousName(res.data.name)
                }
              })
            }
          }}
        >
          {isEdit ? 'Update Configuration' : 'Create Configuration'}
        </Button>
      </div>
    </div>
  )

  const Tab2: FC<any> = () => {
    const [ipdAttributeName, setIdpAttributeName] = useState<string>('')
    const [djangoAttributeName, setDjangoAttributeName] =
      useState<samlAttributeType>(samlAttributes[0])
    const [CreateSamlAttributeMapping, { error: errorAttributeCreation }] =
      useCreateSamlAttributeMappingMutation()
    return (
      <div className='create-feature-tab mt-3'>
        <InputGroup
          title={'SAML Attribute Name*'}
          tooltip='This is the attribute name where you want to store the information received from the SAML identity provider'
          tooltipPlace='right'
          component={
            <Select
              value={djangoAttributeName}
              placeholder='Select a SAML attribute name'
              options={samlAttributes}
              onChange={(m: samlAttributeType) => {
                setDjangoAttributeName(m)
              }}
              className='mb-4 react-select'
            />
          }
        />
        <InputGroup
          className='mt-2'
          title='IDP Attribute Name*'
          data-test='attribute-name'
          tooltip='This is the specific value of the attribute sent by the SAML identity provider'
          tooltipPlace='right'
          value={ipdAttributeName}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
            setIdpAttributeName(Utils.safeParseEventValue(event))
          }}
          inputProps={{
            className: 'full-width',
          }}
          type='text'
          name='Name*'
        />
        <div className='text-right'>
          <Button
            disabled={!ipdAttributeName}
            className='text-right'
            onClick={() => {
              CreateSamlAttributeMapping({
                body: {
                  django_attribute_name: djangoAttributeName?.value ?? '',
                  idp_attribute_name: ipdAttributeName,
                  saml_configuration: data?.id,
                },
              })
            }}
          >
            Add Attribute
          </Button>
        </div>
        {errorAttributeCreation && (
          <div className='mt-2'>
            <ErrorMessage error={errorAttributeCreation} />
          </div>
        )}
        <SAMLAttributeMappingTable samlConfigurationId={data?.id || 0} />
      </div>
    )
  }

  return (
    <>
      {!isEdit ? (
        Tab1
      ) : (
        <Tabs uncontrolled>
          <TabItem
            tabLabel={
              <Row className='justify-content-center'>Basic Configuration</Row>
            }
          >
            {Tab1}
          </TabItem>
          <TabItem
            tabLabel={
              <Row className='justify-content-center'>Attribute Mapping</Row>
            }
          >
            <div className='create-feature-tab px-3'>
              <Tab2 />
            </div>
          </TabItem>
        </Tabs>
      )}
    </>
  )
}
export default CreateSAML
