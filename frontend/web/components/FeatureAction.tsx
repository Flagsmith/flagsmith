import { FC, useCallback, useLayoutEffect, useRef, useState } from 'react'
import classNames from 'classnames'

import useOutsideClick from 'common/useOutsideClick'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import Permission from 'common/providers/Permission'
import Button from './base/forms/Button'
import Icon from './Icon'

interface FeatureActionProps {
  projectId: string
  featureIndex: number
  readOnly: boolean
  isProtected: boolean
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
  isProtected,
  onCopyName,
  onRemove,
  onShowAudit,
  onShowHistory,
  projectId,
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

  return (
    <div className='feature-action'>
      <div ref={btnRef}>
        <Button
          style={{
            lineHeight: 0,
            padding: isCompact ? '0.625rem' : '0.875rem',
          }}
          className={classNames('btn btn-with-icon', {
            'btn-sm': isCompact,
          })}
          data-test={`feature-action-${featureIndex}`}
          onClick={() => setIsOpen(true)}
        >
          <Icon
            name='more-vertical'
            width={isCompact ? 16 : 18}
            fill='#6837FC'
          />
        </Button>
      </div>

      {isOpen && (
        <div ref={listRef} className='feature-action__list'>
          <div
            className='feature-action__item'
            onClick={() => handleActionClick('copy')}
          >
            <Icon name='copy' width={18} fill='#9DA4AE' />
            <span>Copy Feature Name</span>
          </div>
          {!hideAudit && (
            <div
              className='feature-action__item'
              data-test={`feature-audit-${featureIndex}`}
              onClick={() => handleActionClick('audit')}
            >
              <Icon name='list' width={18} fill='#9DA4AE' />
              <span>Show Audit Logs</span>
            </div>
          )}

          {!hideHistory && (
            <div
              className='feature-action__item'
              data-test={`feature-history-${featureIndex}`}
              onClick={() => handleActionClick('history')}
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
                        onClick={() => handleActionClick('remove')}
                      >
                        <Icon name='trash-2' width={18} fill='#9DA4AE' />
                        <span>Remove feature</span>
                      </div>
                    }
                  >
                    {isProtected &&
                      '<span>This feature has been tagged as <bold>protected</bold>, <bold>permanent</bold>, <bold>do not delete</bold>, or <bold>read only</bold>. Please remove the tag before attempting to delete this flag.</span>'}
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
