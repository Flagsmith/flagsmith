import React, { FC, ReactNode } from 'react'
import classNames from 'classnames'
import { Tag as TTag } from 'common/types/responses'
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
  const toggle = () => selectable && onToggle(tag)

  return (
    <div
      className={classNames('tag-row d-flex align-items-center gap-2', {
        'tag-row--disabled': disabled,
        'tag-row--selectable': selectable,
      })}
      onClick={toggle}
      onKeyDown={(e) => {
        // Arrow keys walk the list; a list of rows is one thing to move
        // through, not one tab stop per row.
        const step =
          e.key === 'ArrowDown'
            ? 'nextElementSibling'
            : 'previousElementSibling'
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
          const next = e.currentTarget[step]
          if (next instanceof HTMLElement) {
            e.preventDefault()
            next.focus()
          }
          return
        }
        if (!selectable) return
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          toggle()
        }
      }}
      role={selectable ? 'checkbox' : undefined}
      aria-checked={selectable ? checked : undefined}
      tabIndex={selectable ? 0 : undefined}
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
      {trailing && <div className='tag-row__actions'>{trailing}</div>}
    </div>
  )
}

export default TagRow
