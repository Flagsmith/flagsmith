import React, { FC, useCallback, useEffect, useState } from 'react'
import PanelSearch from 'components/PanelSearch'
import Button from 'components/base/forms/Button'
import { useUpdateEnvironmentMutation } from 'common/services/useEnvironment'
import { Metadata } from 'common/types/responses'
import Utils from 'common/utils/utils'
import Switch from 'components/Switch'
import InputGroup from 'components/base/forms/InputGroup'
import { useGetEntityMetadataFieldsQuery } from 'common/services/useMetadataField'
import { CustomMetadataField } from 'common/types/metadata-field'
import { useGlobalMetadataValidation } from 'common/utils/metadataValidation'

type AddMetadataToEntityProps = {
  isCloningEnvironment?: boolean
  organisationId: number
  projectId: number
  entityContentType: number
  entityId?: number
  entity: string
  envName?: string
  onChange?: (metadata: Metadata[]) => void
  setHasMetadataRequired?: (b: boolean) => void
}

function formatMetadataToApi(fields: CustomMetadataField[]): Metadata[] {
  return fields
    .filter((f) => f.hasValue)
    .map(({ field_value, metadataModelFieldId }) => ({
      field_value: field_value ?? '',
      model_field: metadataModelFieldId as number,
    }))
}

type MetadataErrorResponse = {
  data?: {
    metadata?: Array<{
      non_field_errors?: string[]
      [key: string]: unknown
    }>
  }
}

function getMetadataErrors(error: MetadataErrorResponse): string {
  const metadataErrors = error?.data?.metadata
  if (!metadataErrors) return ''

  return metadataErrors.flatMap((m) => m.non_field_errors ?? []).join('\n')
}

const AddMetadataToEntity: FC<AddMetadataToEntityProps> = ({
  entity,
  entityContentType,
  entityId,
  envName,
  isCloningEnvironment,
  onChange,
  organisationId,
  projectId,
  setHasMetadataRequired,
}) => {
  const { data: initialFields = [], isLoading } =
    useGetEntityMetadataFieldsQuery({
      entityContentType,
      entityId,
      entityType: entity as 'feature' | 'segment' | 'environment',
      organisationId,
      projectId,
    })

  const [metadataFields, setMetadataFields] = useState<CustomMetadataField[]>(
    [],
  )
  const [hasChanges, setHasChanges] = useState(false)

  const { hasUnfilledRequired } = useGlobalMetadataValidation(metadataFields)

  useEffect(() => {
    if (initialFields.length > 0) {
      setMetadataFields(initialFields)
    }
  }, [initialFields])

  useEffect(() => {
    setHasMetadataRequired?.(hasUnfilledRequired)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasUnfilledRequired])

  const handleFieldChange = useCallback(
    (fieldId: number, newValue: string) => {
      setMetadataFields((prev) => {
        const updatedMetadataFields = prev.map((field) =>
          field.id === fieldId
            ? { ...field, field_value: newValue, hasValue: !!newValue }
            : field,
        )

        // Propagate the change to upstream parents
        if (entity !== 'environment' || isCloningEnvironment) {
          const formattedMetadata = formatMetadataToApi(updatedMetadataFields)
          onChange?.(formattedMetadata)
        }

        return updatedMetadataFields
      })
      setHasChanges(true)
    },
    [entity, isCloningEnvironment, onChange],
  )

  const [updateEnvironment] = useUpdateEnvironmentMutation()

  const handleEnvironmentSave = async () => {
    if (!envName || !entityId) return

    const result = await updateEnvironment({
      body: {
        metadata: formatMetadataToApi(metadataFields),
        name: envName,
        project: projectId,
      },
      id: entityId,
    })

    if ('error' in result) {
      toast(getMetadataErrors(result.error as MetadataErrorResponse), 'danger')
    } else {
      toast('Environment Field Updated')
      setHasChanges(false)
    }
  }

  return (
    <FormGroup className='setting'>
      <PanelSearch
        className='mt-1 no-pad'
        isLoading={isLoading}
        header={
          <Row className='table-header'>
            <Row className='table-column flex-1'>Field </Row>
            <Flex className='table-column'>Value</Flex>
          </Row>
        }
        items={metadataFields}
        renderRow={(field: CustomMetadataField) => (
          <MetadataRow
            key={field.id}
            metadata={field}
            onFieldChange={handleFieldChange}
          />
        )}
        renderNoResults={
          <FormGroup>
            No custom fields configured for {entity}s. Add custom fields in your{' '}
            <a
              href={`/organisation/${organisationId}/settings?tab=custom-fields`}
              target='_blank'
              rel='noreferrer'
            >
              Organisation Settings
            </a>
            .
          </FormGroup>
        }
      />
      {entity === 'environment' && !isCloningEnvironment && (
        <div className='text-right'>
          <Button
            theme='primary'
            className='mt-2'
            disabled={
              !metadataFields.length || !hasChanges || hasUnfilledRequired
            }
            onClick={handleEnvironmentSave}
          >
            Save Custom Field
          </Button>
        </div>
      )}
    </FormGroup>
  )
}

type MetadataRowProps = {
  metadata: CustomMetadataField
  onFieldChange: (fieldId: number, value: string) => void
}

const MetadataRow: FC<MetadataRowProps> = ({ metadata, onFieldChange }) => {
  const displayValue =
    metadata.type === 'bool'
      ? metadata.field_value === 'true'
      : metadata.field_value || ''

  const handleChange = (newValue: string | boolean) => {
    const stringValue = metadata.type === 'bool' ? `${newValue}` : `${newValue}`
    onFieldChange(metadata.id, stringValue)
  }
  const isEmpty = !displayValue || displayValue === ''
  const isValidType = Utils.validateMetadataType(metadata.type, displayValue)
  const isValid = isEmpty ? !metadata.isRequiredFor : isValidType

  return (
    <Row className='space list-item clickable py-2'>
      <Flex className='table-column'>
        {metadata.name}
        {metadata.isRequiredFor && '*'}
      </Flex>
      {metadata.type === 'bool' ? (
        <Flex className='flex-row'>
          <Switch
            checked={[true, 'true'].includes(displayValue)}
            onChange={() => {
              const currentBool =
                displayValue === true || displayValue === 'true'
              handleChange(!currentBool)
            }}
          />
        </Flex>
      ) : (
        <Flex className='flex-row mt-1' style={{ minWidth: '300px' }}>
          <InputGroup
            textarea={metadata.type === 'multiline_str'}
            value={displayValue}
            inputProps={{
              style: {
                height: metadata.type === 'multiline_str' ? '65px' : '44px',
                width: '250px',
              },
            }}
            noMargin
            isValid={isValid}
            onChange={(e: InputEvent) => {
              handleChange(Utils.safeParseEventValue(e))
            }}
            type='text'
          />
        </Flex>
      )}
    </Row>
  )
}

export default AddMetadataToEntity
