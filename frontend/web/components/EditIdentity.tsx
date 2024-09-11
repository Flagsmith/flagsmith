import React, { FC, useEffect, useRef, useState } from 'react'
import { Identity } from 'common/types/responses'
import { useUpdateIdentityMutation } from 'common/services/useIdentity'
import Button from './base/forms/Button'

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

  // Handles updating alias when the span loses focus and removing line breaks
  const handleBlur = () => {
    if (aliasRef.current) {
      let updatedAlias = aliasRef.current.textContent || ''
      // Replace line breaks with spaces and trim leading/trailing whitespace
      updatedAlias = updatedAlias.replace(/\n/g, ' ').trim()

      // If the updated alias is empty, revert to the old value
      if (!updatedAlias) {
        aliasRef.current.textContent = alias
      } else if (updatedAlias !== alias) {
        setAlias(updatedAlias)
        onSubmit(updatedAlias)
      }
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

  // Clears the content of the span when clicked (focus)
  const handleFocus = () => {
    if (aliasRef.current) {
      aliasRef.current.textContent = '' // Clear the text content
      aliasRef.current.focus()
    }
  }

  // Handles preventing the Enter key from creating new lines and blurs on Enter
  const handleKeyDown = (e: React.KeyboardEvent<HTMLSpanElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault() // Prevent new line insertion
      aliasRef.current?.blur() // Trigger blur on Enter
    }
  }

  return (
    <>
      <span
        ref={aliasRef}
        className='fw-normal'
        contentEditable={true}
        suppressContentEditableWarning={true}
        onBlur={handleBlur} // Preserve the old alias if no value
        onKeyDown={handleKeyDown} // Prevent new lines on Enter and blur on Enter
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
        onClick={handleFocus} // Clear the span content on click
      >
        Edit
      </Button>
    </>
  )
}

export default EditIdentity
