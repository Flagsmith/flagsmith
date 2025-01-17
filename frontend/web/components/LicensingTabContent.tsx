import { useUploadOrganisationLicenceMutation } from 'common/services/useOrganisationLicensing'
import React, { useEffect, useRef, useState } from 'react'
import Button from './base/forms/Button'
import Utils from 'common/utils/utils'

type LicensingTabContentProps = {
  organisationId: number
}

const LicensingTabContent: React.FC<LicensingTabContentProps> = ({
  organisationId,
}) => {
  const [uploadOrganisationLicence, { error, isLoading, isSuccess }] =
    useUploadOrganisationLicenceMutation()

  const [licence, setLicence] = useState<File | null>(null)
  const [licenceSignature, setLicenceSignature] = useState<File | null>(null)

  const licenceInputRef = useRef<HTMLInputElement>(null)
  const licenceSignatureInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isSuccess) {
      toast('Licence uploaded successfully')
    }

    if (!isSuccess && error?.data) {
      toast(
        Array.isArray(error?.data)
          ? error?.data[0]
          : 'Upload was not successful',
        'danger',
      )
    }
  }, [isSuccess, error])

  const handleUpload = () => {
    if (!licence || !licenceSignature) return
    uploadOrganisationLicence({
      body: { licence, licence_signature: licenceSignature },
      id: organisationId,
    })
  }

  return (
    <div className='mt-4'>
      <h5 className='mb-5'>Upload Licensing Files</h5>
      <form
        className='upload-licensing-tab'
        onSubmit={(e) => {
          Utils.preventDefault(e)
          handleUpload()
        }}
      >
        <FormGroup>
          <input
            type='file'
            ref={licenceInputRef}
            style={{ display: 'none' }}
            onChange={() =>
              setLicence(licenceInputRef.current?.files?.[0] ?? null)
            }
          />
          <input
            type='file'
            ref={licenceSignatureInputRef}
            style={{ display: 'none' }}
            onChange={() =>
              setLicenceSignature(
                licenceSignatureInputRef.current?.files?.[0] ?? null,
              )
            }
          />
          <div className='flex-row'>
            <Button onClick={() => licenceInputRef.current?.click()}>
              Select Licence File
            </Button>
            {!!licence?.name && (
              <p className='mt-auto mb-auto ml-2 fs-small lh-sm'>
                {licence.name}
              </p>
            )}
          </div>
          <div className='flex-row mt-4'>
            <Button onClick={() => licenceSignatureInputRef.current?.click()}>
              Select Signature File
            </Button>
            {!!licenceSignature?.name && (
              <p className='mt-auto mb-auto ml-2 fs-small lh-sm'>
                {licenceSignature.name}
              </p>
            )}
          </div>
          <div className='text-right'>
            <Button
              type='submit'
              data-test='create-feature-btn'
              id='create-feature-btn'
              disabled={!licence || !licenceSignature}
            >
              {isLoading ? 'Uploading' : 'Upload Licensing Files'}
            </Button>
          </div>
        </FormGroup>
      </form>
    </div>
  )
}

export default LicensingTabContent
