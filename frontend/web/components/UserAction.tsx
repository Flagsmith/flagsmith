import { FC, useCallback, useLayoutEffect, useRef, useState } from 'react'
import classNames from 'classnames'

import useOutsideClick from 'common/useOutsideClick'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import Permission from 'common/providers/Permission'
import Button from './base/forms/Button'
import Icon from './Icon'
import ActionButton from './ActionButton'

interface FeatureActionProps {
  canRemove: boolean
  onRemove: () => void
  onEdit: () => void
  canEdit: () => void
}

type ActionType = 'edit' | 'remove'

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

export const FeatureAction: FC<FeatureActionProps> = ({
  canEdit,
  canRemove,
  onEdit,
  onRemove,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false)

  const btnRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

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
      }
      close()
    },
    [close, onRemove, onEdit],
  )

  useOutsideClick(listRef, handleOutsideClick)

  useLayoutEffect(() => {
    if (!isOpen || !listRef.current || !btnRef.current) return
    const listPosition = calculateListPosition(btnRef.current, listRef.current)
    listRef.current.style.top = `${listPosition.top}px`
    listRef.current.style.left = `${listPosition.left}px`
  }, [isOpen])

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
        <ActionButton onClick={() => setIsOpen(true)} />
      </div>

      {isOpen && (
        <div ref={listRef} className='feature-action__list'>
          {!!canEdit && (
            <div
              className='feature-action__item'
              onClick={(e) => {
                e.stopPropagation()
                handleActionClick('edit')
              }}
            >
              <Icon name='edit' width={18} fill='#9DA4AE' />
              <span>Edit Permissions</span>
            </div>
          )}

          {!!canRemove && (
            <div
              className='feature-action__item'
              onClick={(e) => {
                e.stopPropagation()
                handleActionClick('remove')
              }}
            >
              <Icon name='trash-2' width={18} fill='#9DA4AE' />
              <span>Remove</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default FeatureAction
