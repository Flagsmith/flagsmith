import React, { FC, FormEvent, useState } from 'react'
import ProjectProvider from 'common/providers/ProjectProvider'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils' // we need this to make JSX compile
import Button from 'components/base/forms/Button'

type ConfirmRemoveTraitType = {
  trait_key: string
  cb: () => void
}

const ConfirmRemoveTrait: FC<ConfirmRemoveTraitType> = ({ cb, trait_key }) => {
  const [challenge, setChallenge] = useState()
  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (challenge === trait_key) {
      closeModal()
      cb()
    }
  }
  return (
    <ProjectProvider>
      {() => (
        <form id='confirm-remove-trait-modal' onSubmit={submit}>
          <p>
            This will remove trait <strong>{trait_key}</strong> for{' '}
            <strong>all users</strong>.
          </p>
          <InputGroup
            inputProps={{
              className: 'full-width',
              name: 'confirm-trait-key',
            }}
            title='Please type the trait ID to confirm'
            placeholder='Trait ID'
            onChange={(e: InputEvent) => {
              setChallenge(Utils.safeParseEventValue(e))
            }}
          />

          <FormGroup className='text-right'>
            <Button
              id='confirm-remove-trait-btn'
              disabled={challenge !== trait_key}
              type='submit'
            >
              Confirm
            </Button>
          </FormGroup>
        </form>
      )}
    </ProjectProvider>
  )
}

export default ConfirmRemoveTrait
