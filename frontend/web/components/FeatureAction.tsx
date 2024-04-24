import { FC, useCallback, useLayoutEffect, useRef, useState } from 'react'
import classNames from 'classnames'

import useOutsideClick from 'common/useOutsideClick'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import Permission from 'common/providers/Permission'
import Icon from './Icon'
import { Tag } from 'common/types/responses'
import color from 'color'
import { getTagColor } from './tags/Tag'
import ActionButton from './ActionButton'

interface FeatureActionProps {
  projectId: string
  featureIndex: number
  readOnly: boolean
  protectedTags: Tag[] | undefined
  hideAudit: boolean
  hideHistory: boolean
  hideRemove: boolean
  onShowHistory: () => void
  isCompact?: boolean
  onCopyName: () => void
  onShowAudit: () => void
  onRemove: () => void
}

type ActionType = 'copy' | 'audit' | 'history' | 'remove'

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
  featureIndex,
  hideAudit,
  hideHistory,
  hideRemove,
  isCompact,
  onCopyName,
  onRemove,
  onShowAudit,
  onShowHistory,
  projectId,
  protectedTags,
  readOnly,
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
      if (action === 'copy') {
        onCopyName()
      } else if (action === 'history') {
        onShowHistory()
      } else if (action === 'audit') {
        onShowAudit()
      } else if (action === 'remove') {
        onRemove()
      }

      close()
    },
    [close, onCopyName, onRemove, onShowHistory],
  )

  useOutsideClick(listRef, handleOutsideClick)

  useLayoutEffect(() => {
    if (!isOpen || !listRef.current || !btnRef.current) return
    const listPosition = calculateListPosition(btnRef.current, listRef.current)
    listRef.current.style.top = `${listPosition.top}px`
    listRef.current.style.left = `${listPosition.left}px`
  }, [isOpen])

  const isProtected = !!protectedTags?.length
  return (
    <div className='feature-action'>
      <div ref={btnRef}>
        <ActionButton
          onClick={() => setIsOpen(true)}
          data-test={`feature-action-${featureIndex}`}
        />
      </div>

      {isOpen && (
        <div ref={listRef} className='feature-action__list'>
          <div
            className='feature-action__item'
            onClick={(e) => {
              e.stopPropagation()
              handleActionClick('copy')
            }}
          >
            <Icon name='copy' width={18} fill='#9DA4AE' />
            <span>Copy Feature Name</span>
          </div>
          {!hideAudit && (
            <div
              className='feature-action__item'
              data-test={`feature-audit-${featureIndex}`}
              onClick={(e) => {
                e.stopPropagation()
                handleActionClick('audit')
              }}
            >
              <Icon name='list' width={18} fill='#9DA4AE' />
              <span>Show Audit Logs</span>
            </div>
          )}

          {!hideHistory && (
            <div
              className='feature-action__item'
              data-test={`feature-history-${featureIndex}`}
              onClick={(e) => {
                e.stopPropagation()
                handleActionClick('history')
              }}
            >
              <Icon name='clock' width={18} fill='#9DA4AE' />
              <span>Show History</span>
            </div>
          )}

          {!hideRemove && (
            <Permission
              level='project'
              permission='DELETE_FEATURE'
              id={projectId}
            >
              {({ permission: removeFeaturePermission }) =>
                Utils.renderWithPermission(
                  removeFeaturePermission,
                  Constants.projectPermissions('Delete Feature'),
                  <Tooltip
                    title={
                      <div
                        className={classNames('feature-action__item', {
                          'feature-action__item_disabled':
                            !removeFeaturePermission || readOnly || isProtected,
                        })}
                        data-test={`remove-feature-btn-${featureIndex}`}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleActionClick('remove')
                        }}
                      >
                        <Icon name='trash-2' width={18} fill='#9DA4AE' />
                        <span>Remove feature</span>
                      </div>
                    }
                  >
                    {isProtected &&
                      `<span>This feature has been tagged with the permanent tag${
                        protectedTags?.length > 1 ? 's' : ''
                      } ${protectedTags
                        ?.map((tag) => {
                          const tagColor = getTagColor(tag)
                          return `<strong class='chip chip--xs d-inline-block ms-1' style='background:${color(
                            tagColor,
                          ).fade(0.92)};border-color:${color(tagColor).darken(
                            0.1,
                          )};color:${color(tagColor).darken(0.1)};'>
                        ${tag.label}
                      </strong>`
                        })
                        .join('')}. Please remove the tag${
                        protectedTags?.length > 1 ? 's' : ''
                      } before attempting to delete this flag.</span>`}
                  </Tooltip>,
                )
              }
            </Permission>
          )}
        </div>
      )}
    </div>
  )
}

export default FeatureAction
