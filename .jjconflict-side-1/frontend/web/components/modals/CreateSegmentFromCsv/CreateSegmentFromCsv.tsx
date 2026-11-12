import React, { FC, FormEvent, useMemo, useState } from 'react'
import Constants from 'common/constants'
import Format from 'common/utils/format'
import Utils from 'common/utils/utils'
import {
  extractIdentifiers,
  MAX_CSV_FILE_SIZE_BYTES,
  MAX_IDENTIFIER_BYTES,
  parseCsvText,
  toCsvColumn,
  toParsedCsv,
} from 'common/utils/csv'
import { useGetSupportedContentTypeQuery } from 'common/services/useSupportedContentType'
import {
  useCreateCohortMutation,
  useSyncCohortCsvMutation,
} from 'common/services/useCohort'
import { Metadata } from 'common/types/responses'
import AccountStore from 'common/stores/account-store'
import { colorIconSuccess } from 'common/theme/tokens'
import Button from 'components/base/forms/Button'
import Checkbox from 'components/base/forms/Checkbox'
import FieldLabel from 'components/base/forms/FieldLabel'
import InputGroup from 'components/base/forms/InputGroup'
import CsvPreview from 'components/CsvPreview'
import CsvUpload from 'components/CsvUpload'
import EnvironmentSelect from 'components/EnvironmentSelect'
import ErrorMessage from 'components/ErrorMessage'
import Icon from 'components/icons/Icon'
import AddMetadataToEntity from 'components/metadata/AddMetadataToEntity'
import TabItem from 'components/navigation/TabMenu/TabItem'
import Tabs from 'components/navigation/TabMenu/Tabs'
import { CreatedCohort, submitCohortCsv } from './submitCohortCsv'
import './CreateSegmentFromCsv.scss'

type CreateSegmentFromCsvType = {
  projectId: number | string
}

const CreateSegmentFromCsv: FC<CreateSegmentFromCsvType> = ({ projectId }) => {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [environmentId, setEnvironmentId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [rawRows, setRawRows] = useState<string[][]>([])
  const [hasHeaders, setHasHeaders] = useState(true)
  const [selectedColumn, setSelectedColumn] = useState<number | null>(null)
  const [tab, setTab] = useState(0)
  const [metadata, setMetadata] = useState<Metadata[]>([])
  const [createdCohort, setCreatedCohort] = useState<CreatedCohort | null>(null)

  const [createCohort, { error: createError, isLoading: isCreating }] =
    useCreateCohortMutation()
  const [syncCohortCsv, { error: syncError, isLoading: isSyncing }] =
    useSyncCohortCsvMutation()
  const isSaving = isCreating || isSyncing

  const metadataEnable = Utils.getPlansPermission('METADATA')
  const { data: supportedContentTypes } = useGetSupportedContentTypeQuery({
    organisation_id: AccountStore.getOrganisation().id,
  })
  const segmentContentType = useMemo(
    () =>
      supportedContentTypes &&
      Utils.getContentType(supportedContentTypes, 'model', 'segment'),
    [supportedContentTypes],
  )

  const parsed = useMemo(
    () => toParsedCsv(rawRows, hasHeaders),
    [rawRows, hasHeaders],
  )
  const columnIndex = parsed.columns.length === 1 ? 0 : selectedColumn
  const extraction = useMemo(
    () =>
      columnIndex === null
        ? null
        : extractIdentifiers(parsed.rows, columnIndex),
    [parsed.rows, columnIndex],
  )

  // Only the identifier column leaves the browser.
  const csvColumn = useMemo(
    () => (extraction ? toCsvColumn(extraction.identifiers) : ''),
    [extraction],
  )
  // Quoting can expand values, so the generated upload needs its own check.
  const isUploadTooLarge = useMemo(
    () => new Blob([csvColumn]).size > MAX_CSV_FILE_SIZE_BYTES,
    [csvColumn],
  )

  // Identifies the cohort a retry may reuse; see submitCohortCsv.
  const cohortFormKey = JSON.stringify({
    description,
    environmentId,
    metadata,
    name,
  })

  const ignoredRowCount = extraction
    ? extraction.emptyCount +
      extraction.duplicateCount +
      extraction.tooLongCount
    : 0
  const isBlocked = !!extraction && !extraction.identifiers.length
  const canSubmit =
    !!name &&
    !!environmentId &&
    !!file &&
    !!extraction &&
    !isBlocked &&
    !isUploadTooLarge

  const onFile = (newFile: File, text: string) => {
    setFile(newFile)
    setRawRows(parseCsvText(text))
    setSelectedColumn(null)
  }

  const save = async (e: FormEvent) => {
    e.preventDefault()
    if (!canSubmit || !extraction) {
      return
    }
    try {
      const result = await submitCohortCsv({
        createCohort: () =>
          createCohort({
            description: description || undefined,
            environmentApiKey: environmentId,
            metadata,
            name,
            projectId: Number(projectId),
          }).unwrap(),
        createdCohort,
        formKey: cohortFormKey,
        onCohortCreated: setCreatedCohort,
        syncCsv: (cohortId) =>
          syncCohortCsv({
            cohortId,
            environmentApiKey: environmentId,
            file: new File([csvColumn], 'identifiers.csv', {
              type: 'text/csv',
            }),
            has_header: false,
            projectId: Number(projectId),
          }).unwrap(),
      })
      toast(
        `Segment created with ${result.added} ${
          result.added === 1 ? 'identity' : 'identities'
        }`,
        'success',
        10000,
      )
      closeModal()
    } catch (error) {
      console.error('CSV segment creation failed:', error)
    }
  }

  const columnName = columnIndex === null ? '' : parsed.columns[columnIndex]
  let fileError = null
  if (file && !parsed.columns.length) {
    fileError = 'The file appears to be empty.'
  } else if (file && !parsed.rows.length) {
    fileError =
      'No data rows found. If the first row is data rather than a header, untick "First row contains headers".'
  }

  const form = (
    <form className='pt-4' id='create-segment-from-csv-modal' onSubmit={save}>
      <InputGroup
        className='mb-4'
        id='segmentID'
        data-test='segmentID'
        title='Name*'
        value={name}
        inputProps={{
          className: 'full-width',
          maxLength: Constants.forms.maxLength.SEGMENT_ID,
          name: 'id',
        }}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
          setName(
            Format.enumeration.set(Utils.safeParseEventValue(e)).toLowerCase(),
          )
        }}
        isValid={!!name?.length}
        type='text'
        placeholder='E.g. power_users'
      />
      <InputGroup
        className='mb-4'
        value={description}
        inputProps={{ className: 'full-width', name: 'featureDesc' }}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
          setDescription(Utils.safeParseEventValue(e))
        }}
        type='text'
        title='Description'
        placeholder="e.g. 'People who have spent over $100' "
      />
      <div className='mb-4'>
        <FieldLabel htmlFor='environment-select'>Environment</FieldLabel>
        <div className='create-segment-from-csv__select'>
          <EnvironmentSelect
            inputId='environment-select'
            projectId={Number(projectId)}
            size='default'
            value={environmentId}
            onChange={(value) => setEnvironmentId(`${value}`)}
          />
        </div>
        <div className='fs-small text-muted mt-1'>
          The uploaded identities will be targeted in this environment only.
        </div>
      </div>
      <div className='mb-4'>
        <CsvUpload
          value={file}
          maxSizeBytes={MAX_CSV_FILE_SIZE_BYTES}
          rowCount={file ? parsed.rows.length : undefined}
          onChange={onFile}
        />
      </div>
      {!!file && !!parsed.columns.length && (
        <div className='mb-4 d-flex align-items-end justify-content-between gap-3 flex-wrap'>
          {fileError ? (
            <div />
          ) : (
            <div>
              <FieldLabel htmlFor='identifier-column-select'>
                Identifier column
              </FieldLabel>
              <div className='create-segment-from-csv__select'>
                <Select
                  inputId='identifier-column-select'
                  data-test='identifier-column-select'
                  isDisabled={parsed.columns.length === 1}
                  placeholder='Select column'
                  value={
                    columnIndex === null
                      ? null
                      : { label: columnName, value: columnIndex }
                  }
                  options={parsed.columns.map((label, value) => ({
                    label,
                    value,
                  }))}
                  onChange={(option: { value: number }) =>
                    setSelectedColumn(option.value)
                  }
                />
              </div>
            </div>
          )}
          <div className='mb-2'>
            <Checkbox
              label='First row contains headers'
              checked={hasHeaders}
              onChange={setHasHeaders}
            />
          </div>
        </div>
      )}
      {!!fileError && <ErrorMessage error={fileError} />}
      {!!file && !fileError && (
        <>
          {!!parsed.rows.length && (
            <div className='mb-4'>
              <CsvPreview
                columns={parsed.columns}
                rows={parsed.rows}
                selectedColumn={columnIndex}
              />
              {!!extraction && !isBlocked && (
                <div className='d-flex align-items-center gap-2 mt-2 fs-small text-secondary'>
                  <Icon
                    name='checkmark-circle'
                    width={16}
                    fill={colorIconSuccess}
                  />
                  <span>
                    {extraction.identifiers.length.toLocaleString()}{' '}
                    {extraction.identifiers.length === 1
                      ? 'identifier'
                      : 'identifiers'}{' '}
                    detected.
                    {!!ignoredRowCount &&
                      ` ${ignoredRowCount.toLocaleString()} ${
                        ignoredRowCount === 1 ? 'row' : 'rows'
                      } ignored (empty, duplicate, or over ${MAX_IDENTIFIER_BYTES.toLocaleString()} bytes).`}
                  </span>
                </div>
              )}
            </div>
          )}
          {isBlocked && (
            <ErrorMessage
              error={`No valid identifiers found in "${columnName}". Choose a different column or check your file.`}
            />
          )}
          {isUploadTooLarge && (
            <ErrorMessage error='The extracted identifiers exceed the 10MB upload limit. Reduce the number of rows and try again.' />
          )}
        </>
      )}
      {!!(createError || syncError) && (
        <ErrorMessage error={createError || syncError} />
      )}
      <div className='text-right py-3'>
        <Button
          data-test='create-segment'
          disabled={!canSubmit || isSaving}
          type='submit'
        >
          {isSaving ? 'Creating Segment...' : 'Create Segment'}
        </Button>
      </div>
    </form>
  )

  if (!metadataEnable || !segmentContentType?.id) {
    // Outside tabs there is no tab-item padding, so the form provides it.
    return <div className='px-4'>{form}</div>
  }

  return (
    <Tabs value={tab} onChange={(newTab: number) => setTab(newTab)}>
      <TabItem
        tabLabelString='Basic configuration'
        tabLabel='Basic configuration'
      >
        {form}
      </TabItem>
      <TabItem tabLabelString='Custom Fields' tabLabel='Custom Fields'>
        <FormGroup className='pt-4 setting'>
          <InputGroup
            component={
              <AddMetadataToEntity
                organisationId={AccountStore.getOrganisation().id}
                projectId={Number(projectId)}
                entityContentType={segmentContentType.id}
                entity={segmentContentType.model}
                onChange={(m) => setMetadata(m as Metadata[])}
              />
            }
          />
        </FormGroup>
      </TabItem>
    </Tabs>
  )
}

export default CreateSegmentFromCsv
