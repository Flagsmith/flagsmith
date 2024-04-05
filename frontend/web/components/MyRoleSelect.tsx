import { FC } from 'react'
import { useGetRolesQuery } from 'common/services/useRole'
import RolesSelect, { RoleSelectType } from './RolesSelect'
import { PermissionLevel } from 'common/types/requests' // we need this to make JSX compile

type MyRoleSelectType = Omit<RoleSelectType, 'roles'> & {
  orgId: string | number
  level?: PermissionLevel
}

const MyRoleSelect: FC<MyRoleSelectType> = ({ orgId, ...props }) => {
  const { data } = useGetRolesQuery(
    { organisation_id: parseInt(`${orgId}`) },
    { skip: !orgId },
  )
  return <RolesSelect {...props} roles={data?.results} />
}

export default MyRoleSelect
