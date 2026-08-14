import React, { FC, FormEvent, useMemo, useState } from 'react'
import classNames from 'classnames'
import Constants from 'common/constants'
import Format from 'common/utils/format'
import Utils from 'common/utils/utils'
import {
  extractIdentifiers,
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
import Input from 'components/base/forms/Input'
import InputGroup from 'components/base/forms/InputGroup'
import CsvUpload from 'components/CsvUpload'
import EnvironmentSelect from 'components/EnvironmentSelect'
import ErrorMessage from 'components/ErrorMessage'
import Icon from 'components/icons/Icon'
import AddMetadataToEntity from 'components/metadata/AddMetadataToEntity'
import TabItem from 'components/navigation/TabMenu/TabItem'
import Tabs from 'components/navigation/TabMenu/Tabs'
import './CreateSegmentFromCsv.scss'

const PREVIEW_ROW_COUNT = 5
// Mirrors the API's COHORT_CSV_MAX_FILE_SIZE_BYTES.
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

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
  const [createdCohortId, setCreatedCohortId] = useState<number | null>(null)

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
    () => new Blob([csvColumn]).size > MAX_FILE_SIZE_BYTES,
    [csvColumn],
  )

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
      // Keep the created cohort across a failed sync so retrying only syncs.
      let cohortId = createdCohortId
      if (cohortId === null) {
        const cohort = await createCohort({
          description: description || undefined,
          environmentApiKey: environmentId,
          metadata,
          name,
          projectId: Number(projectId),
        }).unwrap()
        cohortId = cohort.id
        setCreatedCohortId(cohortId)
      }
      const result = await syncCohortCsv({
        cohortId,
        environmentApiKey: environmentId,
        file: new File([csvColumn], 'identifiers.csv', { type: 'text/csv' }),
        has_header: false,
        projectId: Number(projectId),
      }).unwrap()
      toast(
        `Segment created with ${result.added} ${
          result.added === 1 ? 'identity' : 'identities'
        }`,
        'success',
        10000,
      )
      closeModal()
    } catch {
      // Errors surface via the mutation error states below.
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
    <form
      className='px-2 pt-4'
      id='create-segment-from-csv-modal'
      onSubmit={save}
    >
      <div className='mb-4'>
        <label htmlFor='segmentID'>Name*</label>
        <Flex>
          <Input
            data-test='segmentID'
            name='id'
            id='segmentID'
            maxLength={Constants.forms.maxLength.SEGMENT_ID}
            value={name}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              setName(
                Format.enumeration
                  .set(Utils.safeParseEventValue(e))
                  .toLowerCase(),
              )
            }}
            isValid={!!name?.length}
            type='text'
            placeholder='E.g. power_users'
          />
        </Flex>
      </div>
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
        <label>Environment</label>
        <div className='create-segment-from-csv__select'>
          <EnvironmentSelect
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
          maxSizeBytes={MAX_FILE_SIZE_BYTES}
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
              <label>Identifier column</label>
              <div className='create-segment-from-csv__select'>
                <Select
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
              <div className='create-segment-from-csv__section-label fw-semibold text-secondary text-uppercase mb-2'>
                Preview (first {PREVIEW_ROW_COUNT} rows)
              </div>
              <div className='create-segment-from-csv__preview rounded-lg overflow-auto'>
                <table className='mb-0 w-100 fs-small'>
                  <thead>
                    <tr>
                      {parsed.columns.map((column, i) => (
                        <th
                          key={i}
                          className={classNames('fw-semibold', {
                            'create-segment-from-csv__cell--selected':
                              i === columnIndex,
                          })}
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {parsed.rows.slice(0, PREVIEW_ROW_COUNT).map((row, i) => (
                      <tr key={i}>
                        {parsed.columns.map((_, j) => (
                          <td
                            key={j}
                            className={classNames({
                              'create-segment-from-csv__cell--selected':
                                j === columnIndex,
                            })}
                          >
                            {row[j]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
                    detected. Duplicates and empty rows will be ignored.
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
    return form
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
        <FormGroup className='px-2 pt-4 setting'>
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
