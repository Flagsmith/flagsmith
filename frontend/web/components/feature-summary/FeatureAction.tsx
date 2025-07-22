import { FC, useCallback, useLayoutEffect, useRef, useState } from 'react'

import useOutsideClick from 'common/useOutsideClick'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import Permission from 'common/providers/Permission'
import Icon from 'components/Icon'
import { Tag } from 'common/types/responses'
import color from 'color'
import { getTagColor } from 'components/tags/Tag'
import ActionButton from 'components/ActionButton'
import ActionItem from 'components/shared/ActionItem'
import { calculateListPosition } from 'common/utils/calculateListPosition'

interface FeatureActionProps {
  projectId: string
  featureIndex: number
  readOnly: boolean
  tags: number[]
  protectedTags: Tag[] | undefined
  hideAudit: boolean
  hideHistory: boolean
  hideRemove: boolean
  onShowHistory: () => void
  onCopyName: () => void
  onShowAudit: () => void
  onRemove: () => void
}

type ActionType = 'copy' | 'audit' | 'history' | 'remove'

export const FeatureAction: FC<FeatureActionProps> = ({
  featureIndex,
  hideAudit,
  hideHistory,
  hideRemove,
  onCopyName,
  onRemove,
  onShowAudit,
  onShowHistory,
  projectId,
  protectedTags,
  readOnly,
  tags,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false)
  const [top, setTop] = useState<number>(0)
  const [left, setLeft] = useState<number>(0)
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
    [close, onCopyName, onRemove, onShowHistory, onShowAudit],
  )

  useOutsideClick(listRef, handleOutsideClick)

  useLayoutEffect(() => {
    if (!isOpen || !listRef.current || !btnRef.current) return
    const { left, top } = calculateListPosition(
      btnRef.current,
      listRef.current,
      true,
    )
    listRef.current.style.top = `${top}px`
    listRef.current.style.left = `${left}px`
    setTop(top)
    setLeft(left)
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
          <ActionItem
            icon={<Icon name='copy' width={18} fill='#9DA4AE' />}
            label='Copy Feature Name'
            handleActionClick={() => {
              handleActionClick('copy')
            }}
            entity='feature'
            index={featureIndex}
            action='copy'
          />
          {!hideAudit && (
            <ActionItem
              icon={<Icon name='list' width={18} fill='#9DA4AE' />}
              label='Show Audit Logs'
              handleActionClick={() => {
                handleActionClick('audit')
              }}
              entity='feature'
              index={featureIndex}
              action='audit'
            />
          )}
          {!hideHistory && (
            <ActionItem
              icon={<Icon name='clock' width={18} fill='#9DA4AE' />}
              label='Show History'
              handleActionClick={() => {
                handleActionClick('history')
              }}
              entity='feature'
              index={featureIndex}
              action='history'
            />
          )}
          {!hideRemove && (
            <Permission
              level='project'
              permission='DELETE_FEATURE'
              tags={tags}
              id={projectId}
            >
              {({ permission: removeFeaturePermission }) =>
                Utils.renderWithPermission(
                  removeFeaturePermission,
                  Constants.projectPermissions('Delete Feature'),
                  <Tooltip
                    title={
                      <ActionItem
                        icon={<Icon name='trash-2' width={18} fill='#9DA4AE' />}
                        label='Remove feature'
                        handleActionClick={() => {
                          handleActionClick('remove')
                        }}
                        action='remove'
                        entity='feature'
                        index={featureIndex}
                        disabled={
                          !removeFeaturePermission || readOnly || isProtected
                        }
                      />
                    }
                  >
                    {isProtected &&
                      `<span>This feature has been tagged with the permanent tag${
                        protectedTags?.length > 1 ? 's' : ''
                      } ${protectedTags
                        ?.map((tag) => {
                          const tagColor = Utils.colour(getTagColor(tag))
                          return `<strong class='chip chip--xs d-inline-block ms-1' style='background:${color(
                            tagColor,
                          ).fade(0.92)};border-color:${tagColor.darken(
                            0.1,
                          )};color:${tagColor.darken(0.1)};'>
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
