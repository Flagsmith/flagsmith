import { Segment, SegmentRule } from 'common/types/responses'
import { AudienceSegment } from 'components/experiments/rollout'

// Copying a split re-salts it against the rollout segment, so it would match a
// different set of identities than the source segment does elsewhere.
const containsPercentageSplit = (rules: SegmentRule[]): boolean =>
  rules.some(
    (rule) =>
      rule.conditions?.some(
        (condition) => condition.operator === 'PERCENTAGE_SPLIT',
      ) || containsPercentageSplit(rule.rules ?? []),
  )

// The server rules the picker can enforce itself, so a choice never dead-ends.
// Anything left over still fails server-side and the caller surfaces that.
export const isSelectableAudienceSegment = (
  segment: Segment,
  environmentId: string,
  selected: AudienceSegment[],
): boolean => {
  if (selected.some((selection) => selection.id === segment.id)) return false
  if (segment.feature) return false
  // A cohort only has members in its own environment, so a cohort from
  // elsewhere would silently match nobody.
  if (segment.cohort && segment.cohort.environment_api_key !== environmentId) {
    return false
  }
  // A rule-less segment compiles to a rule matching everyone, which would widen
  // the audience rather than narrow it; the server refuses it too.
  return !!segment.rules?.length && !containsPercentageSplit(segment.rules)
}
