import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import CopyField from 'components/CopyField'
import InputGroup from 'components/base/forms/InputGroup'
import WarningMessage from 'components/WarningMessage'

type ScimTokenModalProps = {
  token: string
}

const ScimTokenModal: FC<ScimTokenModalProps> = ({ token }) => {
  // Inline confirmation step instead of an openConfirm() popup. The project's
  // openConfirm clobbers `global.closeModal` while mounted and doesn't restore
  // it, which breaks the parent modal after Cancel. Inline avoids the stacked
  // modal entirely — and gives the user a clearer pause before discarding the
  // only chance to copy the token.
  const [isConfirming, setIsConfirming] = useState(false)

  return (
    <>
      <WarningMessage warningMessage='Copy this token now — it cannot be retrieved later. Store it somewhere secure before closing this dialogue.' />
      <InputGroup
        title='SCIM bearer token'
        className='mt-3'
        component={
          <CopyField
            value={token}
            className='font-monospace'
            data-test='scim-token-value'
          />
        }
      />
      {isConfirming ? (
        <div className='mt-4 d-flex align-items-center justify-content-end gap-2'>
          <span className='me-auto text-muted'>
            Have you saved the token? It cannot be retrieved later.
          </span>
          <Button
            theme='secondary'
            onClick={() => setIsConfirming(false)}
            data-test='scim-token-cancel'
          >
            Cancel
          </Button>
          <Button
            onClick={() => closeModal()}
            data-test='scim-token-confirm-done'
          >
            Yes, I&apos;ve saved it
          </Button>
        </div>
      ) : (
        <div className='text-right mt-4'>
          <Button
            onClick={() => setIsConfirming(true)}
            data-test='scim-token-done'
          >
            Done
          </Button>
        </div>
      )}
    </>
  )
}

export default ScimTokenModal
