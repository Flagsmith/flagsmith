import React, { FC, useMemo, useState } from 'react'
import {
  extractIdentifiers,
  MAX_CSV_FILE_SIZE_BYTES,
  MAX_IDENTIFIER_BYTES,
  parseCsvText,
  toCsvColumn,
  toParsedCsv,
} from 'common/utils/csv'
import { useSyncCohortCsvMutation } from 'common/services/useCohort'
import { colorIconSuccess, colorIconWarning } from 'common/theme/tokens'
import Button from 'components/base/forms/Button'
import Checkbox from 'components/base/forms/Checkbox'
import FieldLabel from 'components/base/forms/FieldLabel'
import CsvPreview from 'components/CsvPreview'
import CsvUpload from 'components/CsvUpload'
import ErrorMessage from 'components/ErrorMessage'
import Icon from 'components/icons/Icon'

type CohortCsvSyncType = {
  cohortId: number
  environmentApiKey: string
  projectId: number | string
  isSyncing: boolean
}

const CohortCsvSync: FC<CohortCsvSyncType> = ({
  cohortId,
  environmentApiKey,
  isSyncing,
  projectId,
}) => {
  const [file, setFile] = useState<File | null>(null)
  const [rawRows, setRawRows] = useState<string[][]>([])
  const [hasHeaders, setHasHeaders] = useState(true)
  const [selectedColumn, setSelectedColumn] = useState<number | null>(null)

  const [syncCohortCsv, { error: syncError, isLoading: isSaving }] =
    useSyncCohortCsvMutation()

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

  const ignoredRowCount = extraction
    ? extraction.emptyCount +
      extraction.duplicateCount +
      extraction.tooLongCount
    : 0
  const isBlocked = !!extraction && !extraction.identifiers.length
  const canSubmit =
    !!file && !!extraction && !isBlocked && !isUploadTooLarge && !isSyncing

  const onFile = (newFile: File, text: string) => {
    setFile(newFile)
    setRawRows(parseCsvText(text))
    setSelectedColumn(null)
  }

  const reset = () => {
    setFile(null)
    setRawRows([])
    setSelectedColumn(null)
    setHasHeaders(true)
  }

  const submit = async () => {
    if (!canSubmit) {
      return
    }
    try {
      const result = await syncCohortCsv({
        cohortId,
        environmentApiKey,
        file: new File([csvColumn], 'identifiers.csv', { type: 'text/csv' }),
        has_header: false,
        projectId: Number(projectId),
      }).unwrap()
      toast(
        `Synchronisation started: ${result.added.toLocaleString()} to add, ${result.removed.toLocaleString()} to remove`,
        'success',
        10000,
      )
      reset()
    } catch (error) {
      console.error('Cohort CSV sync failed:', error)
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

  return (
    <div className='d-flex flex-column mx-0 gap-2'>
      <div>
        <FieldLabel>Update the list</FieldLabel>
        <div className='fs-small text-muted'>
          {isSyncing
            ? 'Uploads are disabled while a synchronisation is in progress.'
            : "Uploading a new file re-synchronises this segment's identities."}
        </div>
      </div>
      <CsvUpload
        value={file}
        disabled={isSyncing}
        maxSizeBytes={MAX_CSV_FILE_SIZE_BYTES}
        rowCount={file ? parsed.rows.length : undefined}
        onChange={onFile}
      />
      {!!file && !!parsed.columns.length && (
        <div className='d-flex align-items-end justify-content-between gap-3 flex-wrap'>
          {fileError ? (
            <div />
          ) : (
            <div>
              <FieldLabel htmlFor='identifier-column-select'>
                Identifier column
              </FieldLabel>
              <div className='cohort-segment-detail__select'>
                <Select
                  inputId='identifier-column-select'
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
      {!!file && !fileError && !!parsed.rows.length && (
        <CsvPreview
          columns={parsed.columns}
          rows={parsed.rows}
          selectedColumn={columnIndex}
        />
      )}
      {!!extraction && !fileError && !isBlocked && (
        <div className='cohort-segment-detail__review rounded-lg bg-surface-muted p-3 d-flex flex-column mx-0 gap-2 fs-small'>
          <div className='d-flex align-items-center gap-2'>
            <Icon name='checkmark-circle' width={16} fill={colorIconSuccess} />
            <span className='text-secondary'>
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
          <div className='d-flex align-items-center gap-2'>
            <Icon name='warning' width={16} fill={colorIconWarning} />
            <span className='text-muted'>
              Identities missing from the new file lose this segment on
              synchronisation.
            </span>
          </div>
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
      {!!syncError && <ErrorMessage error={syncError} />}
      {!!file && (
        <div className='d-flex justify-content-end gap-2 mt-2'>
          <Button theme='secondary' onClick={reset}>
            Cancel
          </Button>
          <Button disabled={!canSubmit || isSaving} onClick={submit}>
            {isSaving ? 'Synchronising...' : 'Synchronise'}
          </Button>
        </div>
      )}
    </div>
  )
}

export default CohortCsvSync
