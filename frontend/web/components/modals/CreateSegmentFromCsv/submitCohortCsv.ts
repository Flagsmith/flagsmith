// A created cohort belongs to the form state that created it.
export type CreatedCohort = {
  id: number
  formKey: string
}

export type SubmitCohortCsvArgs<TSyncResult> = {
  // The cohort created by an earlier attempt, kept so a retry only syncs.
  createdCohort: CreatedCohort | null
  // Fingerprint of the inputs that feed cohort creation.
  formKey: string
  createCohort: () => Promise<{ id: number }>
  syncCsv: (cohortId: number) => Promise<TSyncResult>
  onCohortCreated: (cohort: CreatedCohort) => void
}

// Two-step save: create the cohort, then sync the CSV. A cohort left behind by
// a failed sync is reused only while the inputs that created it are unchanged,
// so an edited retry never syncs against the previous form's cohort.
// onCohortCreated fires before the sync so a failed sync can still retry.
export async function submitCohortCsv<TSyncResult>({
  createCohort,
  createdCohort,
  formKey,
  onCohortCreated,
  syncCsv,
}: SubmitCohortCsvArgs<TSyncResult>): Promise<TSyncResult> {
  let cohortId =
    createdCohort?.formKey === formKey ? createdCohort.id : undefined
  if (cohortId === undefined) {
    cohortId = (await createCohort()).id
    onCohortCreated({ formKey, id: cohortId })
  }
  return syncCsv(cohortId)
}
