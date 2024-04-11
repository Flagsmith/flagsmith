import React, { FC, useEffect, useState } from 'react'
import PanelSearch from 'components/PanelSearch'
import Button from 'components/base/forms/Button'
import { useGetMetadataModelFieldListQuery } from 'common/services/useMetadataModelField'
import { useGetMetadataFieldListQuery } from 'common/services/useMetadataField'
import {} from 'common/services/useFeatureSegment'
import InputGroup from 'components/base/forms/InputGroup'
import { MetadataField, Metadata } from 'common/types/responses'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import {
  useUpdateProjectFlagMutation,
  useGetProjectFlagQuery,
} from 'common/services/useProjectFlag'

type CustomMetadataField = MetadataField & {
  metadataModelFieldId: number | string | null
}

type AddMetadataToEntityType = {
  organisationId: string
  projectId: string
  entityContentType: number
  entityId: string
  entity: number | string
  createMetadataField: () => void
  updateMetadata: () => void
}

type MetadataFieldSelectType = {
  label: string
  modelFieldId: number
  value: string
}
const AddMetadataToEntity: FC<AddMetadataToEntityType> = ({
  entity,
  entityContentType,
  entityId,
  organisationId,
  projectId,
}) => {
  const { data: metadataFieldList, isSuccess: metadataFieldListLoaded } =
    useGetMetadataFieldListQuery({
      organisation: organisationId,
    })
  const {
    data: metadataModelFieldList,
    isSuccess: metadataModelFieldListLoaded,
  } = useGetMetadataModelFieldListQuery({
    organisation_id: organisationId,
  })

  const { data: projectFeatureData } = useGetProjectFlagQuery(
    {
      id: entityId,
      project: projectId,
    },
    { skip: entity !== 'feature' },
  )

  const [updateMetadataProjectFeature] = useUpdateProjectFlagMutation()

  const [
    metadataFieldsAssociatedtoEntity,
    setMetadataFieldsAssociatedtoEntity,
  ] = useState<CustomMetadataField[]>()

  const [metadataFieldsSelected, setMetadataFieldsSelected] =
    useState<MetadataFieldSelectType>()

  const [fieldValue, setFieldValue] = useState<string>('')

  const updateEntityMetadata = (modelFieldId: number, fieldValue: string) => {
    if (entity === 'feature') {
      updateMetadataProjectFeature({
        body: {
          metadata: [{ field_value: fieldValue, model_field: modelFieldId }],
        },
        feature_id: entityId,
        project_id: projectId,
      })
    }
  }

  useEffect(() => {
    if (
      metadataFieldList &&
      metadataFieldListLoaded &&
      metadataModelFieldList &&
      metadataModelFieldListLoaded
    ) {
      const metadataForContentType = metadataFieldList.results
        .filter((meta) => {
          return metadataModelFieldList.results.some((item) => {
            return (
              item.field === meta.id && item.content_type === entityContentType
            )
          })
        })
        .map((meta) => {
          const matchingItem = metadataModelFieldList.results.find((item) => {
            return (
              item.field === meta.id && item.content_type === entityContentType
            )
          })
          return {
            ...meta,
            metadataModelFieldId: matchingItem ? matchingItem.id : null,
          }
        })
      console.log('DEBUG: metadataForContentType:', metadataForContentType)
      setMetadataFieldsAssociatedtoEntity(metadataForContentType)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    metadataFieldList,
    metadataFieldListLoaded,
    metadataModelFieldList,
    metadataModelFieldListLoaded,
  ])
  return (
    <>
      <FormGroup className='mt-4 setting'>
        <Row className='cols-md-2'>
          <div style={{ width: '250px' }}>
            <InputGroup
              title={'Metadata Field'}
              component={
                <Select
                  placeholder='Select the Metadata Field'
                  options={(metadataFieldsAssociatedtoEntity || []).map(
                    (v: CustomMetadataField) =>
                      ({
                        label: v.name,
                        modelFieldId: v.metadataModelFieldId,
                        value: `${v.id}`,
                      } as MetadataFieldSelectType),
                  )}
                  onChange={(v: MetadataFieldSelectType) => {
                    setMetadataFieldsSelected(v)
                  }}
                  className='mb-4 react-select'
                />
              }
            />
          </div>
          <Row className='flex-wrap'>
            {!!metadataFieldsSelected && (
              <Input
                value={fieldValue}
                onChange={(e: InputEvent) =>
                  setFieldValue(Utils.safeParseEventValue(e))
                }
                className='mr-2'
                style={{ width: '420px' }}
                placeholder='Metadata Value'
                // search
              />
            )}
            {!!metadataFieldsSelected && (
              <Button
                theme='primary'
                onClick={() => {
                  updateEntityMetadata(
                    metadataFieldsSelected.modelFieldId,
                    fieldValue,
                  )
                }}
              >
                Create Metadata
              </Button>
            )}
          </Row>
        </Row>
      </FormGroup>
      <PanelSearch
        className='mt-1 no-pad'
        header={
          <Row className='table-header'>
            <Flex className='table-column px-3'>Metadata</Flex>
            <Flex className='flex-row'>
              <Flex className='table-column'>Value</Flex>
            </Flex>
            <Flex className='table-column'>Delete</Flex>
          </Row>
        }
        items={projectFeatureData?.metadata}
        renderRow={(m: Metadata) => {
          return (
            <Row className='space list-item clickable py-2'>
              <Flex className='table-column px-3'>{'test'}</Flex>
              <Flex className='flex-row'>
                <Flex className='table-column'>{m.field_value}</Flex>
              </Flex>
              <Flex className='table-column'>Delete</Flex>
            </Row>
          )
        }}
      />
    </>
  )
}

export default AddMetadataToEntity
