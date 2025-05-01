import React, { FC, useMemo } from 'react'
import { renderToString } from 'react-dom/server'

import Tooltip from './Tooltip'
import { DerivedPermission } from 'common/types/responses'

import Icon from './Icon'

type DerivedPermissionsListType = {
  derivedPermissions: DerivedPermission
  numberToTruncate?: number
}

const DerivedTag = ({
  name,
  type,
}: {
  name: string
  type: 'group' | 'role'
}) => {
  return (
    <div className='chip me-2 chip--xs bg-primary text-white'>
      <Row>
        <div className='mr-1'>
          <Icon
            fill='white'
            width={12}
            height={12}
            name={type === 'group' ? 'people' : 'award'}
          />
        </div>
        <div>{name}</div>
      </Row>
    </div>
  )
}

const DerivedPermissionsList: FC<DerivedPermissionsListType> = ({
  derivedPermissions,
  numberToTruncate = 3,
}) => {
  const { items, truncatedItems } = useMemo(() => {
    if (!derivedPermissions?.groups && !derivedPermissions?.roles) {
      return {
        items: [],
        truncatedItems: [],
      }
    }

    const groups =
      derivedPermissions?.groups?.map((group) => ({
        ...group,
        type: 'group' as const,
      })) ?? []
    const roles =
      derivedPermissions?.roles?.map((role) => ({
        ...role,
        type: 'role' as const,
      })) ?? []
    const derivedList = [...groups, ...roles]

    const items =
      derivedList && derivedList.length
        ? derivedList.slice(0, numberToTruncate)
        : []

    return {
      items,
      truncatedItems: (derivedList || []).slice(numberToTruncate),
    }
  }, [numberToTruncate, derivedPermissions])

  if (!items?.length) return null

  return (
    <div className='flex-row gap-1 align-items-center'>
      {items.map((value, i) => (
        <DerivedTag key={i} name={value.name} type={value.type} />
      ))}
      {!!truncatedItems.length && (
        <Tooltip
          title={
            <span className='chip me-2 chip--xs bg-primary text-white'>
              +{truncatedItems.length}
            </span>
          }
        >
          {renderToString(
            <div className='d-flex flex-wrap gap-1'>
              {truncatedItems.map((v, i) => (
                <DerivedTag key={i} name={v.name} type={v.type} />
              ))}
            </div>,
          )}
        </Tooltip>
      )}
    </div>
  )
}

export default DerivedPermissionsList
