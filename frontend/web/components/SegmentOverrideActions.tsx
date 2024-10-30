import { FC, useCallback, useLayoutEffect, useRef, useState } from 'react'
import classNames from 'classnames'

import useOutsideClick from 'common/useOutsideClick'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import Permission from 'common/providers/Permission'
import Button from './base/forms/Button'
import Icon from './Icon'
import ActionButton from './ActionButton'

interface SegmentOverrideActionProps {
  canRemove: boolean
  onRemove: () => void
  onEdit: () => void
  hideViewSegment?: void
  onCopyValue: () => void
  canEdit: boolean
  canCopyValue: boolean
}

type ActionType = 'edit' | 'remove' | 'copy'

function calculateListPosition(
  btnEl: HTMLElement,
  listEl: HTMLElement,
): { top: number; left: number } {
  const top = btnEl.offsetTop + btnEl.offsetHeight
  const left = btnEl.offsetLeft + btnEl.offsetWidth - listEl.offsetWidth
  return { left, top }
}

export const SegmentOverrideAction: FC<SegmentOverrideActionProps> = ({
  canCopyValue,
  canEdit,
  canRemove,
  hideViewSegment,
  onCopyValue,
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
      } else if (action === 'copy') {
        onCopyValue()
      }
      close()
    },
    [close, onRemove, onCopyValue, onEdit],
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
        <span>Remove Override</span>
      </Button>
    )
  }

  if (!!canEdit && !canRemove && !hideViewSegment) {
    return (
      <Button onClick={() => handleActionClick('edit')} size='small'>
        View Segment
      </Button>
    )
  }

  if (!canEdit && !canRemove) {
    return null
  }

  return (
    <div className='position-relative'>
      <div ref={btnRef}>
        <ActionButton
          onClick={() => {
            setIsOpen(true)
          }}
        />
      </div>

      {isOpen && (
        <div
          onMouseDown={(e) => {
            e.stopPropagation()
          }}
          onClick={(e) => e.stopPropagation()}
          ref={listRef}
          className='feature-action__list'
        >
          {!!canEdit && !hideViewSegment && (
            <div
              className='feature-action__item'
              onClick={(e) => {
                e.stopPropagation()
                handleActionClick('edit')
              }}
            >
              <Icon name='eye' width={18} fill='#9DA4AE' />
              <span>View segment</span>
            </div>
          )}
          {!!canCopyValue && (
            <div
              className='feature-action__item'
              onClick={(e) => {
                e.stopPropagation()
                handleActionClick('copy')
              }}
            >
              <Icon name='copy' width={18} fill='#9DA4AE' />
              <span>Set value from environment</span>
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
              <span>Remove Override</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SegmentOverrideAction
