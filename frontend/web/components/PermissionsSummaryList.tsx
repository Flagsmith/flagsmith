import React, { FC, useMemo } from 'react'
import Tooltip from './Tooltip'
import { RolePermission, UserPermission } from 'common/types/responses'
import Format from 'common/utils/format'
import classNames from 'classnames'
import { sortBy } from 'lodash'

type PermissionsSummaryListType = {
  isAdmin?: boolean
  permissions: RolePermission['permissions'] | null | undefined
  numberToTruncate?: number
}

type PermissionSummaryItemType = {
  value: RolePermission['permissions'][number]
  isAdmin?: boolean
}

const getPermissionString = (v: RolePermission['permissions'][number]) =>
  `${Format.enumeration.get(v.permission_key)}${v.tags?.length ? `*` : ''}`

export const PermissionSummaryItem: FC<PermissionSummaryItemType> = ({
  isAdmin,
  value,
}) => {
  return (
    <div
      className={classNames('chip chip--xs', {
        'bg-white text-success border-success bg-opacity-10':
          isAdmin || !value.tags?.length,
        'bg-white text-warning border-warning bg-opacity-10':
          !isAdmin && value.tags?.length,
      })}
    >
      {isAdmin ? 'Administrator' : getPermissionString(value)}
    </div>
  )
}

const PermissionsSummaryList: FC<PermissionsSummaryListType> = ({
  isAdmin,
  numberToTruncate = 3,
  permissions,
}) => {
  const { items, truncatedItems } = useMemo(() => {
    if (isAdmin) {
      return {
        items: [{ permission_key: 'Administrator', tags: [] }],
        truncatedItems: [],
      }
    }
    if (!permissions) return { items: [], truncatedItems: [] }

    const sortedPermissions = sortBy(permissions, (v) => -v.tags?.length)

    const items =
      sortedPermissions && sortedPermissions.length
        ? sortedPermissions.slice(0, numberToTruncate)
        : []

    return {
      items,
      truncatedItems: (sortedPermissions || []).slice(numberToTruncate),
    }
  }, [isAdmin, numberToTruncate, permissions])

  const truncatedHasLimitedAccess = truncatedItems?.find((v) => v.tags?.length)
  return (
    <div className='flex-row gap-1 align-items-center'>
      {items.map((value, i) => (
        <PermissionSummaryItem value={value} key={i} />
      ))}
      {!!truncatedItems.length && (
        <Tooltip
          title={
            <span
              className={classNames('chip chip--xs', {
                'bg-white text-success border-success bg-opacity-10':
                  !truncatedHasLimitedAccess,
                'bg-white text-warning border-warning bg-opacity-10':
                  truncatedHasLimitedAccess,
              })}
            >
              +{truncatedItems.length}
            </span>
          }
        >
          {`<div class='d-flex flex-wrap gap-1'>${truncatedItems
            .map(
              (v) => `<div
              class='${classNames('chip chip--xs', {
                'bg-success text-success border-success bg-opacity-10':
                  !v.tags?.length,
                'bg-warning text-warning border-warning bg-opacity-10':
                  v.tags?.length,
              })}'
          >
            ${getPermissionString(v)}
          </div>`,
            )
            .join('')}</div>`}
        </Tooltip>
      )}
    </div>
  )
}

export default PermissionsSummaryList
