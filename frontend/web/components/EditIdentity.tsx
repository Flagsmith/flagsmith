import React, { FC, useEffect, useRef, useState } from 'react'
import classNames from 'classnames'
import { Identity } from 'common/types/responses'
import { useUpdateIdentityMutation } from 'common/services/useIdentity'
import { useHasPermission } from 'common/providers/Permission'
import { EnvironmentPermission } from 'common/types/permissions.types'
import Button from './base/forms/Button'
import { Icon } from './icons'
import ErrorMessage from './ErrorMessage'
import GhostInput from './base/forms/GhostInput'

type EditIdentityType = {
  data: Identity
  environmentId: string
  onComplete?: () => void
}

const EditIdentity: FC<EditIdentityType> = ({ data, environmentId }) => {
  const [alias, setAlias] = useState(data.dashboard_alias)
  const aliasRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setAlias(data?.dashboard_alias)
  }, [data])

  const [updateIdentity, { error, isLoading }] = useUpdateIdentityMutation({})

  const { permission: canEditAlias } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: EnvironmentPermission.ADMIN,
  })

  const handleBlur = () => {
    onSubmit(alias)
  }

  const onSubmit = (updatedAlias?: string) => {
    if (!isLoading) {
      updateIdentity({
        data: { ...data, dashboard_alias: updatedAlias },
        environmentId,
      })
    }
  }

  const handleFocus = () => {
    aliasRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLSpanElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      aliasRef.current?.blur()
    }
  }

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value.toLowerCase()
    setAlias(newValue.replace(/\n/g, ' ').trim())
  }

  if (!canEditAlias) {
    return (
      <span className={classNames('fw-normal', { 'text-muted': !alias })}>
        {alias || 'None'}
      </span>
    )
  }

  return (
    <>
      <GhostInput
        ref={aliasRef}
        value={alias}
        onChange={handleInput}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        placeholder='None'
      />
      <Button
        disabled={!data}
        theme='text'
        className='text-action'
        onClick={handleFocus}
      >
        Edit
        <Icon name='edit' width={16} />
      </Button>
      <ErrorMessage error={error} />
    </>
  )
}

export default EditIdentity
