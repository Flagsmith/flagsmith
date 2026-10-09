// How dependency changes reach an environment: written directly, held for a
// change request, or not at all where change requests run on v1 versioning,
// which #8449 does not support.
export type DependenciesMode = 'direct' | 'changeRequest' | 'readOnly'

export const getDependenciesMode = (
  requiresChangeRequests: boolean,
  isVersioned: boolean,
): DependenciesMode => {
  if (!requiresChangeRequests) return 'direct'
  return isVersioned ? 'changeRequest' : 'readOnly'
}
