import { FC } from 'react'
import { useGetGithubReposQuery } from 'common/services/useGithub'
import GroupSelect, { GroupSelectType } from './GroupSelect' // we need this to make JSX compile

type MyReposSelectType = {
  orgId: string
}

const MyReposSelect: FC<MyReposSelectType> = ({ orgId }) => {
  const { data } = useGetGithubReposQuery({ orgId })
  return <GroupSelect {...props} groups={data?.results} />
}

export default MyReposSelect
