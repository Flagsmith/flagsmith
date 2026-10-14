import { FC } from 'react'
import { useGetFeatureIdsStagedQuery } from 'common/services/useFeatureDependency'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { useFeatureStates } from 'common/hooks/useFeatureStates'
import ChangeRequestDependencyChanges from './ChangeRequestDependencyChanges'
import Panel from 'components/base/grid/Panel'
import ErrorMessage from 'components/ErrorMessage'

type DiffDependenciesProps = {
  changeRequestId: number
  environmentId: string
  projectId: string
}

const FeatureDependencyChanges: FC<
  DiffDependenciesProps & { featureId: number }
> = ({ changeRequestId, environmentId, featureId, projectId }) => {
  const { data: feature } = useGetProjectFlagQuery({
    id: featureId,
    project: Number(projectId),
  })
  // Whether each prerequisite is on now, so a reviewer can see an added one
  // that would hold this feature off.
  const states = useFeatureStates({
    environmentId,
    projectId: Number(projectId),
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
      <ChangeRequestDependencyChanges
        environmentId={environmentId}
        featureId={featureId}
        changeRequestId={changeRequestId}
        // Until the states are known, no column rather than every row "No".
        isEnabled={
          states.isLoading || states.isError ? undefined : states.isEnabled
        }
      />
    </Panel>
  )
}

// The prerequisite changes staged in a change request, per feature.
const DiffDependencies: FC<DiffDependenciesProps> = ({
  changeRequestId,
  environmentId,
  projectId,
}) => {
  const { data: featureIds, isError } = useGetFeatureIdsStagedQuery({
    changeRequestId,
  })
  // Otherwise a failed list reads as no dependency changes.
  if (isError) {
    return (
      <div className='mt-4'>
        <ErrorMessage error='Could not load the dependency changes in this change request.' />
      </div>
    )
  }
  return (
    <>
      {featureIds?.map((featureId) => (
        <FeatureDependencyChanges
          key={featureId}
          changeRequestId={changeRequestId}
          environmentId={environmentId}
          featureId={featureId}
          projectId={projectId}
        />
      ))}
    </>
  )
}

export default DiffDependencies
