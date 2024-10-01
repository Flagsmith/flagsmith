import React, { FC, useEffect, useRef, useState } from 'react'
import { Identity } from 'common/types/responses'
import { useUpdateIdentityMutation } from 'common/services/useIdentity'
import Button from './base/forms/Button'
import ErrorMessage from './ErrorMessage'

type EditIdentityType = {
  data: Identity
  environmentId: string
  onComplete?: () => void
}

const EditIdentity: FC<EditIdentityType> = ({ data, environmentId }) => {
  const [alias, setAlias] = useState(data.dashboard_alias)
  const aliasRef = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    setAlias(data?.dashboard_alias)
  }, [data])

  const [updateIdentity, { error, isLoading }] = useUpdateIdentityMutation({})

  const handleBlur = () => {
    if (aliasRef.current) {
      const updatedAlias = (aliasRef.current.textContent || '')
        .replace(/\n/g, ' ')
        .trim()
        .toLowerCase()

      aliasRef.current.textContent = alias
      setAlias(updatedAlias)
      onSubmit(updatedAlias)
    }
  }

  const onSubmit = (updatedAlias: string) => {
    if (!isLoading && updatedAlias) {
      updateIdentity({
        data: { ...data, dashboard_alias: updatedAlias },
        environmentId,
      })
    }
  }

  const handleFocus = () => {
    if (aliasRef.current) {
      aliasRef.current.textContent = ''
      aliasRef.current.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLSpanElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      aliasRef.current?.blur()
    }
  }

  return (
    <>
      <span
        ref={aliasRef}
        className='fw-normal'
        contentEditable={true}
        suppressContentEditableWarning={true}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        role='textbox'
        aria-label='Alias'
      >
        {alias || 'None'}
      </span>
      <Button
        disabled={!data}
        iconSize={18}
        theme='text'
        className='ms-2 text-primary'
        iconRightColour='primary'
        iconRight={'edit'}
        onClick={handleFocus}
      >
        Edit
      </Button>
      <ErrorMessage>{error}</ErrorMessage>
    </>
  )
}

export default EditIdentity
