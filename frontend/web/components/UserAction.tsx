import { FC, useCallback, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

import useOutsideClick from 'common/useOutsideClick'
import Button from './base/forms/Button'
import Icon from './Icon'
import ActionButton from './ActionButton'

interface FeatureActionProps {
  canRemove: boolean
  onRemove: () => void
  onEdit: () => void
  canEdit: boolean
  onInspectPermissions?: () => void
}

type ActionType = 'edit' | 'remove' | 'inspect'

type ActionDropdownProps = {
  isOpen: boolean
  canEdit?: boolean
  canRemove?: boolean
  btnRef: React.RefObject<HTMLDivElement>
  onAction: (action: ActionType) => void
  onOutsideClick: () => void
}

function calculateListPosition(
  btnEl: HTMLElement,
  listEl: HTMLElement,
): { top: number; left: number } {
  const listPosition = listEl.getBoundingClientRect()
  const btnPosition = btnEl.getBoundingClientRect()
  const pageTop = window.visualViewport?.pageTop ?? 0
  return {
    left: btnPosition.right - listPosition.width,
    top: pageTop + btnPosition.bottom,
  }
}

const ActionDropdown = ({
  btnRef,
  canEdit,
  canRemove,
  isOpen,
  onAction,
  onOutsideClick,
}: ActionDropdownProps) => {
  const dropDownRef = useRef<HTMLDivElement>(null)

  useOutsideClick(dropDownRef, onOutsideClick)

  useLayoutEffect(() => {
    if (!isOpen || !dropDownRef.current || !btnRef.current) return
    const listPosition = calculateListPosition(
      btnRef.current,
      dropDownRef.current,
    )
    dropDownRef.current.style.top = `${listPosition.top}px`
    dropDownRef.current.style.left = `${listPosition.left}px`
  }, [btnRef, isOpen, dropDownRef])

  if (!isOpen) return null

  return createPortal(
    <div ref={dropDownRef} className='feature-action__list'>
      {true && (
        <div
          className='feature-action__item'
          onClick={(e) => {
            e.stopPropagation()
            onAction('inspect')
          }}
        >
          <Icon name='search' width={18} fill='#9DA4AE' />
          <span>Inspect permissions</span>
        </div>
      )}
      {!!canEdit && (
        <div
          className='feature-action__item'
          onClick={(e) => {
            e.stopPropagation()
            onAction('edit')
          }}
        >
          <Icon name='edit' width={18} fill='#9DA4AE' />
          <span>Manage user</span>
        </div>
      )}

      {!!canRemove && (
        <div
          className='feature-action__item'
          onClick={(e) => {
            e.stopPropagation()
            onAction('remove')
          }}
        >
          <Icon name='trash-2' width={18} fill='#9DA4AE' />
          <span>Remove</span>
        </div>
      )}
    </div>,
    document.body,
  )
}

export const FeatureAction: FC<FeatureActionProps> = ({
  canEdit,
  canRemove,
  onEdit,
  onInspectPermissions,
  onRemove,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false)

  const btnRef = useRef<HTMLDivElement>(null)

  const close = useCallback(() => setIsOpen(false), [])

  const handleOutsideClick = useCallback(
    () => isOpen && close(),
    [close, isOpen],
  )

  const handleActionClick = useCallback(
    (action: ActionType) => {
      if (action === 'edit') {
        onEdit()
      } else if (action === 'remove') {
        onRemove()
      } else if (action === 'inspect') {
        onInspectPermissions?.()
      }
      close()
    },
    [close, onRemove, onEdit, onInspectPermissions],
  )

  if (!canEdit && !!canRemove) {
    return (
      <Button onClick={onRemove} size='small' className='btn-with-icon'>
        <Icon name='trash-2' width={16} fill='#656D7B' />
      </Button>
    )
  }

  if (!!canEdit && !canRemove) {
    return (
      <Button
        onClick={() => handleActionClick('edit')}
        size='small'
        className='btn-with-icon'
      >
        <Icon name='edit' width={16} fill='#656D7B' />
      </Button>
    )
  }

  if (!canEdit && !canRemove) {
    return null
  }

  return (
    <div>
      <div ref={btnRef}>
        <ActionButton size='small' onClick={() => setIsOpen(true)} />
      </div>
      <ActionDropdown
        isOpen={isOpen}
        canEdit={canEdit}
        canRemove={canRemove}
        btnRef={btnRef}
        onAction={handleActionClick}
        onOutsideClick={handleOutsideClick}
      />
    </div>
  )
}

export default FeatureAction
