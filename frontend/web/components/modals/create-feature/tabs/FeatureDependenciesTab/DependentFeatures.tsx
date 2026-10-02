import { FC } from 'react'
import { DependencyEdge } from 'common/types/responses'
import DependentFeaturesTable from './DependentFeaturesTable'
import { DependentsEmptyState } from './DependenciesEmptyStates'

type DependentFeaturesProps = {
  featureName: string
  edges: DependencyEdge[]
  hasPrerequisites: boolean
  onSelect: (featureId: number) => void
}

const DependentFeatures: FC<DependentFeaturesProps> = ({
  edges,
  featureName,
  hasPrerequisites,
  onSelect,
}) => (
  <>
    <h5 className='mt-4 mb-2'>Dependent features</h5>

    {edges.length ? (
      <>
        {/* Describes the rows, so it only appears when there are rows. The
            heading already says what they are; this says what it costs them. */}
        <div className='text-muted mb-3'>
          These flags are off while <strong>{featureName}</strong> is off.
        </div>
        <div className='feature-dependencies__panel'>
          <DependentFeaturesTable
            edges={edges}
            onSelect={(edge) => onSelect(edge.feature.id)}
          />
        </div>
      </>
    ) : (
      <div className='feature-dependencies__panel'>
        <DependentsEmptyState
          featureName={featureName}
          hasPrerequisites={hasPrerequisites}
        />
      </div>
    )}
  </>
)

export default DependentFeatures
