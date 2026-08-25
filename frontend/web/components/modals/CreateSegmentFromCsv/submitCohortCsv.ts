export type SubmitCohortCsvArgs<TSyncResult> = {
  // The cohort created by an earlier failed attempt, so a retry only syncs.
  existingCohortId: number | null
  createCohort: () => Promise<{ id: number }>
  syncCsv: (cohortId: number) => Promise<TSyncResult>
  onCohortCreated: (cohortId: number) => void
}

// Two-step save: create the cohort unless one survived a failed attempt,
// then sync the CSV. onCohortCreated fires before the sync so a failed sync
// still records the cohort id for retry.
export async function submitCohortCsv<TSyncResult>({
  createCohort,
  existingCohortId,
  onCohortCreated,
  syncCsv,
}: SubmitCohortCsvArgs<TSyncResult>): Promise<TSyncResult> {
  let cohortId = existingCohortId
  if (cohortId === null) {
    cohortId = (await createCohort()).id
    onCohortCreated(cohortId)
  }
  return syncCsv(cohortId)
}
