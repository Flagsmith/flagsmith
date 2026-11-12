import React, { FC } from 'react'
import { FeaturesTableFilters } from 'components/pages/features/components/FeaturesTableFilters'
import { excludeTag } from 'components/pages/feature-lifecycle/constants'
import type { FilterState } from 'common/types/featureFilters'

type LifecycleFiltersHeaderProps = {
  projectId: number
  filters: FilterState
  hasFilters: boolean
  isLoading?: boolean
  onFilterChange: (updates: Partial<FilterState>) => void
  onClearFilters: () => void
}

const LifecycleFiltersHeader: FC<LifecycleFiltersHeaderProps> = (props) => (
  <FeaturesTableFilters {...props} excludeTag={excludeTag} />
)

export default LifecycleFiltersHeader
