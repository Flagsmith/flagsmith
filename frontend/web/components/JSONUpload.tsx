import { FC, useCallback, useState } from 'react'
import DropIcon from './svg/DropIcon'
import Button from './base/forms/Button'
import { useDropzone } from 'react-dropzone'

type DropAreaType = {
  onChange: (file: File, json: Record<string, any>) => void
}

const JSONUpload: FC<DropAreaType> = ({ onChange }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [file, setFile] = useState<File | null>(null)

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
          onChange(file, json)
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
      setFile(acceptedFiles[0])
    }
  }, [])
  const { getInputProps, getRootProps, isDragActive } = useDropzone({
    accept: {
      'application/json': [],
    },
    multiple: false,
    onDrop,
  })

  return file ? (
    <Row>
      <div {...getRootProps()}>
        <input {...getInputProps()} />
        <div className='flex-row droparea droparea--condensed text-center'>
          <DropIcon />
          <div className='ml-2'>
            <strong>{file.name}</strong>
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
        <div className='text-muted mb-4'>.json File</div>
        <Button>Select File</Button>
      </div>
    </div>
  )
}

export default JSONUpload
