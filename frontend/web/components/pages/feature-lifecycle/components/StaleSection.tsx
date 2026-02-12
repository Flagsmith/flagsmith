import React, { FC, useCallback, useState } from 'react'
import Button from 'components/base/forms/Button'
import DropdownMenu from 'components/base/DropdownMenu'
import SectionShell from './SectionShell'
import { useClientPagination } from 'components/pages/feature-lifecycle/hooks/useClientPagination'
import { useCreateCleanupIssueMutation } from 'common/services/useGithubIntegration'
import { useLazyGetFeatureCodeReferencesQuery } from 'common/services/useCodeReferences'
import WarningMessage from 'components/WarningMessage'
import AccountStore from 'common/stores/account-store'
import Utils from 'common/utils/utils'
import type { ProjectFlag } from 'common/types/responses'
import type { FilterState } from 'common/types/featureFilters'

type StaleSectionProps = {
  flags: ProjectFlag[]
  isLoading: boolean
  error: unknown
  projectId: number
  filters: FilterState
  hasFilters: boolean
  onFilterChange: (updates: Partial<FilterState>) => void
  onClearFilters: () => void
}

const StaleSection: FC<StaleSectionProps> = ({
  error,
  filters,
  flags,
  hasFilters,
  isLoading,
  onClearFilters,
  onFilterChange,
  projectId,
}) => {
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [createCleanupIssue] = useCreateCleanupIssueMutation()
  const [triggerGetCodeReferences] = useLazyGetFeatureCodeReferencesQuery()

  const { goToPage, nextPage, pageItems, paging, prevPage } =
    useClientPagination({ items: flags })

  const handleSelect = useCallback((flag: ProjectFlag) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(flag.id)) {
        next.delete(flag.id)
      } else {
        next.add(flag.id)
      }
      return next
    })
  }, [])

  const isSelected = useCallback(
    (flag: ProjectFlag) => selectedIds.has(flag.id),
    [selectedIds],
  )

  const handleCopyCleanupPrompt = useCallback(
    async (flag: ProjectFlag) => {
      try {
        const { data } = await triggerGetCodeReferences({
          featureId: flag.id,
          projectId,
        })

        const codeReferences =
          data
            ?.flatMap((repo) =>
              repo.code_references.map(
                (ref) => `- ${ref.file_path}:${ref.line_number}`,
              ),
            )
            .join('\n') || 'No code references found.'

        const prompt = [
          'We need to clean up feature flag usage in the code.',
          `Our goal is to delete references of the "${flag.name}" feature.`,
          'We need to delete the feature flag check so that the code path is no longer guarded by the feature flag.',
          '',
          'These are the occurrences of this feature flag in this repository:',
          codeReferences,
        ].join('\n')

        Utils.copyToClipboard(prompt, 'Cleanup prompt copied to clipboard')
      } catch {
        toast('Failed to fetch code references', 'danger')
      }
    },
    [triggerGetCodeReferences, projectId],
  )

  const handleCreateCleanupIssue = useCallback(
    (flag: ProjectFlag) => {
      openConfirm({
        body: (
          <div>
            This will create a GitHub issue in{' '}
            <strong>flagsmith/flagsmith</strong> to clean up{' '}
            <strong>{flag.name}</strong>.
            <WarningMessage
              warningMessageClass='d-block mt-4'
              warningMessage={
                <>
                  Cleaning up a feature flag means removing the flag checks from
                  code so that the code behaves as if the flag were{' '}
                  <strong>enabled for everyone</strong>, allowing you to then
                  delete the feature in Flagsmith.
                </>
              }
            />
          </div>
        ),
        onYes: async () => {
          try {
            await createCleanupIssue({
              body: {
                feature_id: flag.id,
              },
              organisation_id: AccountStore.getOrganisation()?.id,
            }).unwrap()
            toast(<span>Cleanup issue created.</span>)
          } catch {
            toast('Failed to create cleanup issue', 'danger')
          }
        },
        title: 'Create Cleanup Issue',
        yesText: 'Create Issue',
      })
    },
    [createCleanupIssue],
  )

  return (
    <SectionShell
      id='stale-list'
      projectId={projectId}
      items={pageItems}
      paging={paging}
      isLoading={isLoading}
      error={error}
      filters={filters}
      hasFilters={hasFilters}
      onFilterChange={onFilterChange}
      onClearFilters={onClearFilters}
      emptyLabel='No stale features with code references found.'
      nextPage={nextPage}
      prevPage={prevPage}
      goToPage={goToPage}
      isSelected={isSelected}
      onSelect={handleSelect}
      renderActions={(flag) => (
        <DropdownMenu
          items={[
            {
              icon: 'github',
              label: 'Create Cleanup Issue',
              onClick: () => handleCreateCleanupIssue(flag),
            },
            {
              icon: 'copy',
              label: 'Copy Cleanup AI Prompt',
              onClick: () => handleCopyCleanupPrompt(flag),
            },
          ]}
        />
      )}
      header={
        selectedIds.size > 0 ? (
          <Row className='mb-2 justify-content-end'>
            <Button
              data-test='cleanup-code-btn'
              onClick={() => {
                // TODO: implement code cleanup action
              }}
            >
              {`Cleanup Code (${selectedIds.size})`}
            </Button>
          </Row>
        ) : undefined
      }
    />
  )
}

export default StaleSection
