import { FC, useCallback } from 'react'
import DropIcon from './svg/DropIcon'
import Button from './base/forms/Button'
import { useDropzone } from 'react-dropzone'
import { DropAreaType } from './JSONUpload'

const XMLUpload: FC<DropAreaType> = ({ onChange, value }) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const reader = new FileReader()

    reader.addEventListener(
      'load',
      () => {
        try {
          onChange(acceptedFiles[0], reader.result as string)
        } catch (e) {
          toast('File is not valid XML')
        }
      },
      false,
    )

    if (acceptedFiles[0]) {
      reader.readAsText(acceptedFiles[0])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const { getInputProps, getRootProps } = useDropzone({
    accept: {
      'text/xml': [],
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
              <strong>Drag a file or click to select a file</strong>
            </div>
            <div className='text-muted fs-small mb-4'>XML File</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default XMLUpload
