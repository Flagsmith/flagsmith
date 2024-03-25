import { FC } from 'react'
import { useGetGithubReposQuery } from 'common/services/useGithub'

type MyReposSelectType = {
  orgId: string
  onChange: () => void
}

const MyReposSelect: FC<MyReposSelectType> = ({ orgId }) => {
  const { data } = useGetGithubReposQuery({ orgId })
  return <></>
}

export default MyReposSelect
