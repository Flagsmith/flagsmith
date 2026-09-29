import React, { FC, ReactNode } from 'react'
import classNames from 'classnames'
import { Tag as TTag } from 'common/types/responses'
import BareButton from 'components/base/forms/BareButton'
import Tag from 'components/tags/Tag'
import Icon from 'components/icons/Icon'
import './TagRow.scss'

type TagRowProps = {
  /** Omitted when the row is not selectable. */
  checked?: boolean
  disabled?: boolean
  onToggle?: (tag: TTag) => void
  tag: TTag
  /** Whatever the list wants on the right: a menu, a usage count. */
  trailing?: ReactNode
}

// Arrow keys walk the list: a list of rows is one thing to move through, not
// one tab stop per row.
const moveFocus = (e: React.KeyboardEvent<HTMLButtonElement>) => {
  if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return
  const row = e.currentTarget.parentElement
  const sibling =
    e.key === 'ArrowDown'
      ? row?.nextElementSibling
      : row?.previousElementSibling
  const target = sibling?.querySelector('.tag-row__select')
  if (target instanceof HTMLElement) {
    e.preventDefault()
    target.focus()
  }
}

/**
 * One tag in a list of tags. Marked with a trailing checkmark, as every other
 * list in the app marks selection. Anything in `trailing` appears on hover and
 * on focus, taking the right edge, with the mark sliding left to make room.
 */
const TagRow: FC<TagRowProps> = ({
  checked,
  disabled,
  onToggle,
  tag,
  trailing,
}) => {
  const selectable = checked !== undefined && !!onToggle && !disabled

  return (
    <div
      className={classNames('tag-row d-flex align-items-center', {
        'tag-row--disabled': disabled,
      })}
    >
      {/* Only the selecting part is the control. `trailing` is a sibling, so
          its menu button is not inside this one. */}
      <BareButton
        className='tag-row__select d-flex align-items-center gap-2'
        disabled={!selectable}
        onClick={() => onToggle?.(tag)}
        onKeyDown={moveFocus}
        role={selectable ? 'checkbox' : undefined}
        aria-checked={selectable ? checked : undefined}
      >
        <Tag className='me-0' disabled={disabled} tag={tag} />
        <span className='tag-row__spacer' />
        {checked !== undefined && (
          <Icon
            className={classNames('tag-row__mark text-default', {
              'opacity-0': !checked,
            })}
            name='checkmark'
          />
        )}
      </BareButton>
      {trailing && <div className='tag-row__actions'>{trailing}</div>}
    </div>
  )
}

export default TagRow
