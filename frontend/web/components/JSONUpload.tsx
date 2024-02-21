import { FC, useCallback, useState } from 'react'
import DropIcon from './svg/DropIcon'
import Button from './base/forms/Button'
import { useDropzone } from 'react-dropzone'

type DropAreaType = {
  value: File | null
  onChange: (file: File, json: Record<string, any>) => void
}

const JSONUpload: FC<DropAreaType> = ({ onChange, value }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setIsLoading(true)
    setError('')
    // Do something with the files
    const reader = new FileReader()

    reader.addEventListener(
      'load',
      () => {
        let json
        try {
          json = JSON.parse(reader.result)
          onChange(acceptedFiles[0], json)
        } catch (e) {
          setError('File is not valid JSON')
        }
      },
      false,
    )

    reader.addEventListener(
      'error',
      () => {
        setIsLoading(false)
        setError('Error reading file')
      },
      false,
    )
    reader.addEventListener(
      'abort',
      () => {
        setIsLoading(false)
      },
      false,
    )

    if (acceptedFiles[0]) {
      reader.readAsText(acceptedFiles[0])
    }
  }, [])
  const { getInputProps, getRootProps, isDragActive } = useDropzone({
    accept: {
      'application/json': [],
    },
    multiple: false,
    onDrop,
  })

  return (
    <div className='cursor-pointer'>
      {value ? (
        <Row>
          <div {...getRootProps()}>
            <input {...getInputProps()} />
            <div className='flex-row droparea droparea--condensed text-center'>
              <DropIcon width={24} height={24} />
              <div className='ml-2'>
                <strong className={'fs-small'}>{value.name}</strong>
              </div>
              <Button size='small' className={'ml-2'}>
                Select File
              </Button>
            </div>
          </div>
        </Row>
      ) : (
        <div {...getRootProps()}>
          <input {...getInputProps()} />
          <div className='droparea text-center'>
            <DropIcon />
            <div className='mb-2'>
              <strong>Select a file or drag and drop here</strong>
            </div>
            <div className='text-muted fs-small mb-4'>JSON File</div>
            <Button>Select File</Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default JSONUpload
