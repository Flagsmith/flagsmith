import React, { FC } from 'react'
import Tooltip from './Tooltip'
import Utils from 'common/utils/utils'

type PermissionsSummaryListType = {
  isAdmin: boolean
  permissions: string[] | null | undefined
  numberToTruncate?: number
}

const PermissionsSummaryList: FC<PermissionsSummaryListType> = ({
  isAdmin,
  numberToTruncate = 3,
  permissions,
}) => {
  const { items, truncatedItems } = Utils.getPermissionList(
    isAdmin,
    permissions,
    numberToTruncate,
  )

  return (
    <div className='flex-row gap-1 align-items-center'>
      {items.map((value: string, i: number) => (
        <div key={i} className='chip chip--xs'>
          {value}
        </div>
      ))}
      {!!truncatedItems.length && (
        <Tooltip
          title={
            <span className='chip chip--xs'>+{truncatedItems.length}</span>
          }
        >
          {truncatedItems.join(', ')}
        </Tooltip>
      )}
    </div>
  )
}

export default PermissionsSummaryList
