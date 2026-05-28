import React, { FC, useState } from 'react'
import OnboardingChip from 'web/components/onboarding-quickstart/OnboardingChip'
import ConceptDrawer from 'web/components/onboarding-quickstart/ConceptDrawer'
import {
  CONCEPT_ITEMS,
  ConceptItemId,
} from 'web/components/pages/onboarding-quickstart/data/presets'

const OnboardingChipWithDrawer: FC = () => {
  const [isOpen, setIsOpen] = useState(false)
  // First-flag concept is auto-ticked when the user reaches the AHA moment.
  // Persisting completion across sessions is a follow-up — for the POC
  // we start from the AHA milestone already completed.
  const [completedIds, setCompletedIds] = useState<ConceptItemId[]>([
    'first-flag',
  ])

  const activeId =
    CONCEPT_ITEMS.find((item) => !completedIds.includes(item.id))?.id ?? null

  const handleItemClick = (id: ConceptItemId) => {
    setCompletedIds((existing) =>
      existing.includes(id) ? existing : [...existing, id],
    )
  }

  if (completedIds.length === CONCEPT_ITEMS.length) {
    // Drawer has graduated the user — chip retires.
    return null
  }

  return (
    <>
      <OnboardingChip
        completedCount={completedIds.length}
        isPulsing={completedIds.length < CONCEPT_ITEMS.length}
        totalCount={CONCEPT_ITEMS.length}
        onClick={() => setIsOpen(true)}
      />
      <ConceptDrawer
        activeId={activeId}
        completedIds={completedIds}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        onItemClick={handleItemClick}
      />
    </>
  )
}

export default OnboardingChipWithDrawer
