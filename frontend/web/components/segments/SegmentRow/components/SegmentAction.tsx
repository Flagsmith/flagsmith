import { FC, useCallback, useLayoutEffect, useRef, useState } from 'react'
import ActionButton from 'components/ActionButton'
import ActionItem from 'components/shared/ActionItem'
import Icon from 'components/Icon'
import useOutsideClick from 'common/useOutsideClick'
import { calculateListPosition } from 'common/utils/calculateListPosition'

interface SegmentActionProps {
  index: number
  isRemoveDisabled: boolean
  isCloneDisabled: boolean
  onRemove: () => void
  onClone: () => void
}

const SegmentAction: FC<SegmentActionProps> = ({
  index,
  isCloneDisabled = true,
  isRemoveDisabled,
  onClone,
  onRemove,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const btnRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const handleOutsideClick = useCallback(
    () => isOpen && setIsOpen(false),
    [isOpen],
  )
  useOutsideClick(listRef, handleOutsideClick)

  useLayoutEffect(() => {
    if (!isOpen || !listRef.current || !btnRef.current) return
    const { left, top } = calculateListPosition(btnRef.current, listRef.current)
    listRef.current.style.top = `${top}px`
    listRef.current.style.left = `${left}px`
  }, [isOpen])

  return (
    <div className='feature-action'>
      <div ref={btnRef}>
        <ActionButton
          onClick={() => setIsOpen(true)}
          data-test={`segment-action-${index}`}
        />
      </div>
      {isOpen && (
        <div ref={listRef} className='feature-action__list'>
          {!isCloneDisabled && (
            <ActionItem
              icon={<Icon name='copy' width={18} fill='#9DA4AE' />}
              label='Clone Segment'
              handleActionClick={() => {
                onClone()
              }}
              entity='segment'
              index={index}
              disabled={isCloneDisabled}
              action='clone'
            />
          )}
          <ActionItem
            icon={<Icon name='trash-2' width={18} fill='#9DA4AE' />}
            label='Remove Segment'
            handleActionClick={() => {
              onRemove()
            }}
            entity='segment'
            index={index}
            disabled={isRemoveDisabled}
            action='remove'
          />
        </div>
      )}
    </div>
  )
}

export default SegmentAction
