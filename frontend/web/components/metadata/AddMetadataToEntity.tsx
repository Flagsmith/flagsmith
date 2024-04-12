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

type CustomMetadata = (Metadata & CustomMetadataField) | null

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

  const { data: projectFeatureData, isSuccess: projectFeatureDataLoaded } =
    useGetProjectFlagQuery(
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

  const [metadataWithMetadataField, setMergeMetadataWithMetadataField] =
    useState<CustomMetadata[]>()

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
      // Filter metadata fields based on the provided content type
      const metadataForContentType = metadataFieldList.results
        // Filter metadata fields that have corresponding entries in the metadata model field list
        .filter((meta) => {
          return metadataModelFieldList.results.some((item) => {
            return (
              item.field === meta.id && item.content_type === entityContentType
            )
          })
        })
        // Map each filtered metadata field to include additional information from the metadata model field list
        .map((meta) => {
          // Find the matching item in the metadata model field list
          const matchingItem = metadataModelFieldList.results.find((item) => {
            return (
              item.field === meta.id && item.content_type === entityContentType
            )
          })
          // Return the metadata field with additional metadata model field information
          return {
            ...meta,
            metadataModelFieldId: matchingItem ? matchingItem.id : null,
          }
        })
      if (projectFeatureData && projectFeatureDataLoaded) {
        const mergeMetadataWithMetadataField: CustomMetadata[] =
          projectFeatureData?.metadata
            .map((item1) => {
              const matchingItem = metadataForContentType.find(
                (item2) => item1.model_field === item2.metadataModelFieldId,
              )
              return matchingItem ? { ...item1, ...matchingItem } : null
            })
            .filter((item) => item !== null)

        setMergeMetadataWithMetadataField(mergeMetadataWithMetadataField)
      }

      setMetadataFieldsAssociatedtoEntity(metadataForContentType)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    metadataFieldList,
    metadataFieldListLoaded,
    metadataModelFieldList,
    metadataModelFieldListLoaded,
    projectFeatureDataLoaded,
    projectFeatureData,
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
          items={metadataWithMetadataField}
          renderRow={(m: CustomMetadata) => {
            return (
              <Row className='space list-item clickable py-2'>
                <Flex className='table-column px-3'>{m?.description}</Flex>
                <Flex className='flex-row'>
                  <Flex className='table-column'>{m?.field_value}</Flex>
                </Flex>
                <Flex className='table-column'>Delete</Flex>
              </Row>
            )
          }}
        />
      </FormGroup>
    </>
  )
}

export default AddMetadataToEntity
