import { FC, ReactNode } from 'react'
import { DependencyEdge } from 'common/types/responses'
import Constants from 'common/constants'
import Banner from 'components/base/Banner'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Tooltip from 'components/Tooltip'
import ModalHR from 'components/modals/ModalHR'
import BlockedBanner from './BlockedBanner'
import DependentFeatures from './DependentFeatures'
import PrerequisitesTable from './PrerequisitesTable'
import { PrerequisiteRow } from './prerequisiteState'
import { PrerequisitesEmptyState } from './DependenciesEmptyStates'

export const DEPENDENCIES_DOCS_URL =
  'https://docs.flagsmith.com/basic-features/managing-features'

export type FeatureDependenciesViewProps = {
  featureName: string
  environmentName: string
  rows: PrerequisiteRow[]
  dependentEdges: DependencyEdge[]
  canManage: boolean
  // A slot, so this component never fetches and Storybook can render it.
  addControl: ReactNode
  conflict?: string | null
  // Owned by the container, which is where an add resolves.
  isAdding: boolean
  onAddingChange: (isAdding: boolean) => void
  highlightedId?: number
  isRemoving?: number
  onRemove: (edge: DependencyEdge) => void
  onSelectFeature: (featureId: number) => void
}

const FeatureDependenciesView: FC<FeatureDependenciesViewProps> = ({
  addControl,
  canManage,
  conflict,
  dependentEdges,
  environmentName,
  featureName,
  highlightedId,
  isAdding,
  isRemoving,
  onAddingChange,
  onRemove,
  onSelectFeature,
  rows,
}) => {
  const isPrerequisite = !!dependentEdges.length

  return (
    <div className='feature-dependencies'>
      <div className='d-flex align-items-center gap-1 mb-2'>
        <Tooltip
          title={
            <h5 className='mb-0'>
              Flag dependencies <Icon name='info-outlined' />
            </h5>
          }
          place='top'
        >
          {Constants.strings.FEATURE_DEPENDENCIES_DESCRIPTION}
        </Tooltip>
      </div>

      {/* The rule cannot apply to a flag that cannot have prerequisites, so
          the empty state explains that case instead. */}
      {!isPrerequisite && (
        <div className='text-muted mb-3'>
          This flag only serves its own value when every prerequisite below is
          on.{' '}
          <a href={DEPENDENCIES_DOCS_URL} target='_blank' rel='noreferrer'>
            Learn more
          </a>
        </div>
      )}

      {rows.length || isAdding ? (
        <>
          <BlockedBanner environmentName={environmentName} rows={rows} />
          <div className='feature-dependencies__panel'>
            <PrerequisitesTable
              rows={rows}
              canManage={canManage}
              highlightedId={highlightedId}
              isRemoving={isRemoving}
              onRemove={onRemove}
              addRow={
                isAdding && (
                  <tr className='feature-dependencies__add-row'>
                    {/* One cell: the picker has no column to line up with. */}
                    <td colSpan={4}>
                      <div className='feature-dependencies__add-control d-flex align-items-center gap-2'>
                        {addControl}
                        <Button
                          theme='text'
                          onClick={() => onAddingChange(false)}
                        >
                          Cancel
                        </Button>
                      </div>
                    </td>
                  </tr>
                )
              }
            />
          </div>
        </>
      ) : (
        <div className='feature-dependencies__panel'>
          <PrerequisitesEmptyState
            featureName={featureName}
            isPrerequisite={isPrerequisite}
          />
        </div>
      )}

      {/* Warning, not error: nothing failed, a rule is being stated. On
          screen rather than a toast, because the user has to choose again. */}
      {!!conflict && (
        <Banner type='warning' className='mt-3'>
          {conflict}
        </Banner>
      )}

      {!isPrerequisite && canManage && !isAdding && (
        <div className='mt-3'>
          <Button
            theme='outline'
            size='small'
            onClick={() => onAddingChange(true)}
            data-test='add-prerequisite-btn'
          >
            Add prerequisite
          </Button>
        </div>
      )}

      <ModalHR className='mt-4' />

      <DependentFeatures
        featureName={featureName}
        edges={dependentEdges}
        hasPrerequisites={!!rows.length}
        onSelect={onSelectFeature}
      />
    </div>
  )
}

export default FeatureDependenciesView
