import React, { FC, useActionState, useEffect, useRef } from 'react'
import Button from 'components/base/forms/Button'
import ModalHR from 'components/modals/ModalHR'

type CreateServerSideKeyModalProps = {
  environmentName: string
  onSubmit: (name: string) => Promise<void>
}

const CreateServerSideKeyModal: FC<CreateServerSideKeyModalProps> = ({
  environmentName,
  onSubmit,
}) => {
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const timer = setTimeout(() => inputRef.current?.focus(), 500)
    return () => clearTimeout(timer)
  }, [])

  const [error, submitAction, isPending] = useActionState(
    async (_prev: string | null, formData: FormData) => {
      const name = (formData.get('name') as string)?.trim()
      if (!name) return 'Name is required'
      try {
        await onSubmit(name)
        return null
      } catch {
        return 'Failed to create key. Please try again.'
      }
    },
    null,
  )

  return (
    <div>
      <form action={submitAction}>
        <div className='modal-body'>
          <div className='mb-2'>
            This will create a Server-side Environment Key for the environment{' '}
            <strong>{environmentName}</strong>.
          </div>
          <InputGroup
            title='Key Name'
            placeholder='New Key'
            className='mb-2'
            ref={inputRef}
            inputProps={{
              className: 'full-width modal-input',
              name: 'name',
            }}
          />
          {error && <div className='text-danger mt-2'>{error}</div>}
        </div>
        <ModalHR />
        <div className='modal-footer'>
          <Button onClick={closeModal} theme='secondary' className='mr-2'>
            Cancel
          </Button>
          <Button type='submit' disabled={isPending}>
            {isPending ? 'Creating...' : 'Create'}
          </Button>
        </div>
      </form>
    </div>
  )
}

export default CreateServerSideKeyModal
