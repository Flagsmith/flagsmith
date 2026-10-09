import { DependencyEdge, DependencyFeature } from 'common/types/responses'

// A prerequisite held for a change request has no segment until the change
// request is published, so it gets a stand-in.
export const stagedDependencyEdge = (
  featureId: number,
  prerequisite: DependencyFeature,
): DependencyEdge => ({
  feature: { id: featureId, name: '' },
  prerequisite,
  segment: {
    condition_json_path: '',
    id: -prerequisite.id,
    is_system: true,
    name: '',
    rules: [],
  },
})
