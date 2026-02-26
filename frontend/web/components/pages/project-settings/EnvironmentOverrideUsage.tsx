import { FC } from 'react'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'
import UsageBar from 'components/shared/UsageBar'

export type EnvironmentOverrideUsageProps = {
  apiKey: string
  limit: number
  name: string
}

const EnvironmentOverrideUsage: FC<EnvironmentOverrideUsageProps> = ({
  apiKey,
  limit,
  name,
}) => {
  const { data } = useGetEnvironmentQuery({ id: apiKey })
  const usage = data?.total_segment_overrides ?? 0

  return <UsageBar label={name} limit={limit} usage={usage} />
}

export default EnvironmentOverrideUsage
