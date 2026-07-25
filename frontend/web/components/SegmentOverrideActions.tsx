import { FC, useCallback, useLayoutEffect, useRef, useState } from 'react'

import useOutsideClick from 'common/useOutsideClick'
import Button from './base/forms/Button'
import Icon from './icons/Icon'
import ActionButton from './ActionButton'

interface SegmentOverrideActionProps {
  canRemove: boolean
  onRemove: () => void
  onEdit: () => void
  hideViewSegment?: void
  onCopyValue: () => void
  onCompare: () => void
  canEdit: boolean
  canCopyValue: boolean
  canCompare: boolean
}

type ActionType = 'edit' | 'remove' | 'copy' | 'compare'

function calculateListPosition(
  btnEl: HTMLElement,
  listEl: HTMLElement,
): { top: number; left: number } {
  const top = btnEl.offsetTop + btnEl.offsetHeight
  const left = btnEl.offsetLeft + btnEl.offsetWidth - listEl.offsetWidth
  return { left, top }
}

const SegmentOverrideAction: FC<SegmentOverrideActionProps> = ({
  canCompare,
  canCopyValue,
  canEdit,
  canRemove,
  hideViewSegment,
  onCompare,
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
      } else if (action === 'compare') {
        onCompare()
      }
      close()
    },
    [close, onRemove, onCopyValue, onEdit, onCompare],
  )

  useOutsideClick(listRef, handleOutsideClick)

  useLayoutEffect(() => {
    if (!isOpen || !listRef.current || !btnRef.current) return
    const listPosition = calculateListPosition(btnRef.current, listRef.current)
    listRef.current.style.top = `${listPosition.top}px`
    listRef.current.style.left = `${listPosition.left}px`
  }, [isOpen])

  if (!canEdit && !!canRemove && !canCompare) {
    return (
      <Button onClick={onRemove} size='small' className='btn-with-icon'>
        <span>Remove Override</span>
      </Button>
    )
  }

  if (!!canEdit && !canRemove && !hideViewSegment && !canCompare) {
    return (
      <Button onClick={() => handleActionClick('edit')} size='small'>
        View Segment
      </Button>
    )
  }

  if (!canEdit && !canRemove && !canCompare) {
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
          {!!canCompare && (
            <div
              className='feature-action__item'
              onClick={(e) => {
                e.stopPropagation()
                handleActionClick('compare')
              }}
            >
              <Icon name='difference' width={18} />
              <span>Compare</span>
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
