import { FC } from 'react'
import { ChangeRequest } from 'common/types/responses'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { useFeatureStates } from 'common/hooks/useFeatureStates'
import DependencyChangesTable from './DependencyChangesTable'
import { useDependencyChanges } from './useDependencyChanges'
import Panel from 'components/base/grid/Panel'
import ErrorMessage from 'components/ErrorMessage'

type DiffDependenciesProps = {
  changeRequest: ChangeRequest
  environmentId: string
  projectId: string
}

type FeatureDependencyChangesProps = {
  changeRequestId: number
  environmentId: string
  featureId: number
  projectId: string
}

const FeatureDependencyChanges: FC<FeatureDependencyChangesProps> = ({
  changeRequestId,
  environmentId,
  featureId,
  projectId,
}) => {
  const { changes, isError } = useDependencyChanges({
    changeRequestId,
    environmentId,
    featureId,
  })
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

  if (isError) {
    return (
      <div className='mt-4'>
        <ErrorMessage error='Could not load the dependency changes in this change request.' />
      </div>
    )
  }
  // Most change sets only touch values or overrides, so no panel for those.
  if (!changes?.length) return null
  return (
    <Panel
      title={`Dependencies${feature ? `: ${feature.name}` : ''}`}
      className='no-pad mt-4'
    >
      <p className='text-secondary px-3 pt-3 mb-2'>
        Prerequisite changes in this request. Nothing changes until it is
        published.
      </p>
      <DependencyChangesTable
        changes={changes}
        // Until the states are known, no column rather than every row "No".
        isEnabled={
          states.isLoading || states.isError ? undefined : states.isEnabled
        }
      />
    </Panel>
  )
}

// The prerequisite changes staged in a change request, per feature it
// changes.
const DiffDependencies: FC<DiffDependenciesProps> = ({
  changeRequest,
  environmentId,
  projectId,
}) => {
  const featureIds = [
    ...new Set(changeRequest.change_sets?.map(({ feature }) => feature)),
  ]
  return (
    <>
      {featureIds.map((featureId) => (
        <FeatureDependencyChanges
          key={featureId}
          changeRequestId={changeRequest.id}
          environmentId={environmentId}
          featureId={featureId}
          projectId={projectId}
        />
      ))}
    </>
  )
}

export default DiffDependencies
