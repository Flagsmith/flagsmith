import { FC } from 'react'
import { PendingDependencyChanges } from 'common/types/responses'
import { useGetChangeRequestDependencyChangesQuery } from 'common/services/useFeatureDependency'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import DependencyChangesTable from 'components/DependencyChangesTable'
import Panel from 'components/base/grid/Panel'

type DiffDependenciesProps = {
  changeRequestId: number
  projectId: string
}

const FeatureDependencyChanges: FC<
  PendingDependencyChanges & { projectId: string }
> = ({ changes, featureId, projectId }) => {
  const { data: feature } = useGetProjectFlagQuery({
    id: featureId,
    project: Number(projectId),
  })
  return (
    <Panel
      title={`Dependencies${feature ? `: ${feature.name}` : ''}`}
      className='no-pad mt-4'
    >
      <p className='text-secondary px-3 pt-3 mb-2'>
        Prerequisite changes in this request. Nothing changes until it is
        published.
      </p>
      <DependencyChangesTable changes={changes} />
    </Panel>
  )
}

// The prerequisite changes staged in a change request, per feature.
const DiffDependencies: FC<DiffDependenciesProps> = ({
  changeRequestId,
  projectId,
}) => {
  const { data } = useGetChangeRequestDependencyChangesQuery({
    changeRequestId,
  })
  return (
    <>
      {(data ?? []).map((entry) => (
        <FeatureDependencyChanges
          key={entry.featureId}
          {...entry}
          projectId={projectId}
        />
      ))}
    </>
  )
}

export default DiffDependencies
