import { FC } from 'react'
import { useGetMyGroupsQuery } from 'common/services/useMyGroup'
import GroupSelect, { GroupSelectType } from './GroupSelect' // we need this to make JSX compile

type MyGroupsSelectType = Omit<GroupSelectType, 'groups'> & {
  organisationId: number
}

const MyGroupsSelect: FC<MyGroupsSelectType> = ({ organisationId, ...props }) => {
  const { data } = useGetMyGroupsQuery(
    { organisationId: `${organisationId}`, page_size: 1 },
    { skip: !organisationId },
  )
  return <GroupSelect {...props} groups={data?.results} />
}

export default MyGroupsSelect
