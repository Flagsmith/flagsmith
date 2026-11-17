import React, { FC, useMemo } from 'react'
import Tooltip from './Tooltip'
import { RolePermission } from 'common/types/responses'
import Format from 'common/utils/format'
import Chip, { chipClassName } from './base/Chip'
import { sortBy } from 'lodash'

type PermissionsSummaryListType = {
  isAdmin: boolean
  permissions: RolePermission['permissions'] | null | undefined
  numberToTruncate?: number
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
  const getPermissionString = (v: RolePermission['permissions'][number]) =>
    `${Format.enumeration.get(v.permission_key)}${v.tags?.length ? `*` : ''}`

  // Tag-scoped permissions grant limited access.
  const getVariant = (v: RolePermission['permissions'][number]) =>
    v.tags?.length ? 'warning' : 'success'

  const truncatedHasLimitedAccess = truncatedItems?.find((v) => v.tags?.length)
  return (
    <div className='flex-row gap-1 align-items-center'>
      {items.map((value, i) => (
        <Chip key={i} size='xs' variant={getVariant(value)}>
          {getPermissionString(value)}
        </Chip>
      ))}
      {!!truncatedItems.length && (
        <Tooltip
          title={
            <Chip
              size='xs'
              variant={truncatedHasLimitedAccess ? 'warning' : 'success'}
            >
              +{truncatedItems.length}
            </Chip>
          }
        >
          {`<div class='d-flex flex-wrap gap-1'>${truncatedItems
            .map(
              (v) =>
                `<span class='${chipClassName({
                  size: 'xs',
                  variant: getVariant(v),
                })}'>${getPermissionString(v)}</span>`,
            )
            .join('')}</div>`}
        </Tooltip>
      )}
    </div>
  )
}

export default PermissionsSummaryList
