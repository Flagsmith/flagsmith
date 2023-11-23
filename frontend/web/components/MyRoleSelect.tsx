import { FC } from 'react'
import { useGetRolesQuery } from 'common/services/useRole'
import RolesSelect, { RoleSelectType } from './RolesSelect' // we need this to make JSX compile

type MyRoleSelectType = RoleSelectType & {
  orgId: string
}

const MyRoleSelect: FC<MyRoleSelectType> = ({ orgId, ...props }) => {
  const { data } = useGetRolesQuery(
    { organisation_id: orgId },
    { skip: !orgId },
  )
  return <RolesSelect {...props} roles={data?.results} />
}

export default MyRoleSelect
