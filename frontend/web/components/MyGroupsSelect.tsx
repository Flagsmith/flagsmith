import { FC } from 'react'
import { useGetMyGroupsQuery } from 'common/services/useMyGroup'
import GroupSelect, { GroupSelectType } from './GroupSelect' // we need this to make JSX compile

type MyGroupsSelectType = Omit<GroupSelectType, 'groups'> & {
  orgId: string | number
}

const MyGroupsSelect: FC<MyGroupsSelectType> = ({ orgId, ...props }) => {
  const { data } = useGetMyGroupsQuery(
    { orgId: `${orgId}`, page_size: 1 },
    { skip: !orgId },
  )
  return <GroupSelect {...props} groups={data?.results} />
}

export default MyGroupsSelect
