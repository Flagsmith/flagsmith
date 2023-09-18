import { FC } from 'react'
import { useGetMyGroupsQuery } from 'common/services/useMyGroup'
import GroupSelect, { GroupSelectType } from './GroupSelect' // we need this to make JSX compile

type MyGroupsSelectType = GroupSelectType & {
  orgId: string
}

const MyGroupsSelect: FC<MyGroupsSelectType> = ({ orgId, ...props }) => {
  console.log('DEBUG: orgId:', orgId)
  const { data } = useGetMyGroupsQuery({ orgId, page_size: 1 })
  return <GroupSelect {...props} groups={data?.results} />
}

export default MyGroupsSelect
