import { FC, useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { colorIconAction } from 'common/theme/tokens'
import DropIcon from 'components/icons/DropIcon'
import Icon from 'components/icons/Icon'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import './CsvUpload.scss'

export type CsvUploadType = {
  value: File | null
  rowCount?: number
  onChange: (file: File, text: string) => void
}

const formatFileSize = (bytes: number) => {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }
  return `${(bytes / 1024).toFixed(1)} KB`
}

const CsvUpload: FC<CsvUploadType> = ({ onChange, rowCount, value }) => {
  const [error, setError] = useState('')

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setError('')
      const file = acceptedFiles[0]
      if (!file) {
        return
      }
      const reader = new FileReader()
      reader.addEventListener('load', () => {
        onChange(file, `${reader.result}`)
      })
      reader.addEventListener('error', () => {
        setError('Error reading file')
      })
      reader.readAsText(file)
    },
    [onChange],
  )

  const { getInputProps, getRootProps, open } = useDropzone({
    accept: {
      'text/csv': ['.csv'],
    },
    multiple: false,
    noClick: true,
    noKeyboard: true,
    onDrop,
    onDropRejected: () => {
      setError('Please select a CSV file')
    },
  })

  return (
    <div className='csv-upload'>
      <div {...getRootProps()}>
        <input {...getInputProps()} />
        {value ? (
          <div className='csv-upload__file-card d-flex align-items-center gap-3 p-3 rounded-lg bg-surface-default'>
            <span className='csv-upload__file-icon d-inline-flex align-items-center justify-content-center flex-shrink-0 rounded-md bg-surface-action-tint'>
              <Icon name='file-text' width={20} fill={colorIconAction} />
            </span>
            <div className='flex-fill overflow-hidden'>
              <div className='fw-semibold text-truncate'>{value.name}</div>
              <div className='fs-small text-secondary'>
                {formatFileSize(value.size)}
                {typeof rowCount === 'number' &&
                  ` · ${rowCount.toLocaleString()} ${
                    rowCount === 1 ? 'row' : 'rows'
                  }`}
              </div>
            </div>
            <Button theme='outline' onClick={open}>
              Replace file
            </Button>
          </div>
        ) : (
          <div className='csv-upload__droparea text-center rounded-lg'>
            <DropIcon />
            <div className='mt-2 mb-2'>
              <strong>Drag and drop your CSV here</strong>
            </div>
            <div className='text-secondary fs-small mb-3'>
              or browse it from your computer
            </div>
            <Button onClick={open}>Select file</Button>
          </div>
        )}
      </div>
      {!!error && <ErrorMessage error={error} />}
    </div>
  )
}

export default CsvUpload
