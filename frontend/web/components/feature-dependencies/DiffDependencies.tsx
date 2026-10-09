import { FC } from 'react'
import { useGetFeatureIdsStagedQuery } from 'common/services/useFeatureDependency'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import ChangeRequestDependencyChanges from './ChangeRequestDependencyChanges'
import Panel from 'components/base/grid/Panel'

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
      />
    </Panel>
  )
}

// The prerequisite changes staged in a change request, per feature.
const DiffDependencies: FC<DiffDependenciesProps> = (props) => {
  const { data: featureIds } = useGetFeatureIdsStagedQuery({
    changeRequestId: props.changeRequestId,
  })
  return (
    <>
      {(featureIds ?? []).map((featureId) => (
        <FeatureDependencyChanges
          key={featureId}
          {...props}
          featureId={featureId}
        />
      ))}
    </>
  )
}

export default DiffDependencies
