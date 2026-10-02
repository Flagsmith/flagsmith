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
  // The picker is a slot so this stays free of data fetching, which is what
  // lets Storybook render the real markup.
  addControl: ReactNode
  conflict?: string | null
  // Whether the picker row is open. The container owns it, because only the
  // container knows when an add succeeded and the row should close.
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

      {/* The rule is constant, so it stays put. The banner below says what it
          currently resolves to. A flag that cannot have prerequisites is not
          governed by the rule at all, so it gets the empty state's explanation
          instead of a sentence that can never apply to it. */}
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
                    {/* One cell across the whole row: the picker has nothing to
                        line up with, and Cancel does not fit the actions
                        column. */}
                    <td colSpan={4}>
                      <div className='feature-dependencies__add-control'>
                        {addControl}
                        {/* The refusal belonged to the interaction being
                            cancelled, so it goes with it. */}
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

      {/* Nothing failed: the one-layer rule is being stated, so warning rather
          than error. It stays on screen rather than going to a toast because
          the picker is still open and the user has to choose again. It sits
          under the table, where that picker is. */}
      {!!conflict && (
        <Banner type='warning' className='mt-3'>
          {conflict}
        </Banner>
      )}

      {/* The button names what it does; the picker then opens as the last row,
          where the prerequisite it creates will appear. */}
      {!isPrerequisite && canManage && !isAdding && (
        <div className='feature-dependencies__add'>
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
