import { FC } from 'react'
import { useGetRolesQuery } from 'common/services/useRole'
import RolesSelect, { RoleSelectType } from './RolesSelect'
import { PermissionLevel } from 'common/types/requests' // we need this to make JSX compile

type MyRoleSelectType = Omit<RoleSelectType, 'roles'> & {
  organisationId: number
  level?: PermissionLevel
}

const MyRoleSelect: FC<MyRoleSelectType> = ({ organisationId, ...props }) => {
  const { data } = useGetRolesQuery(
    { organisation_id: parseInt(`${organisationId}`) },
    { skip: !organisationId },
  )
  return <RolesSelect {...props} roles={data?.results} />
}

export default MyRoleSelect
