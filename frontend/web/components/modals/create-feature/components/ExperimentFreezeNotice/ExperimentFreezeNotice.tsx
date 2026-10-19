import { FC } from 'react'
import InfoMessage from 'components/InfoMessage'
import Link from 'components/base/link'

type FreezeExperiment = {
  id: number
  name: string
  status: string
}

type ExperimentFreezeNoticeProps = {
  experiment: FreezeExperiment
  projectId: number | string
  environmentId: string
}

const ExperimentFreezeNotice: FC<ExperimentFreezeNoticeProps> = ({
  environmentId,
  experiment,
  projectId,
}) => {
  const experimentUrl = `/project/${projectId}/environment/${environmentId}/experiments/${experiment.id}`

  return (
    <InfoMessage>
      This flag is part of the experiment{' '}
      <Link to={experimentUrl}>
        <strong>{experiment.name}</strong>
      </Link>{' '}
      which is currently {experiment.status}. Editing is restricted to prevent
      skewing experiment results.
    </InfoMessage>
  )
}

export default ExperimentFreezeNotice
