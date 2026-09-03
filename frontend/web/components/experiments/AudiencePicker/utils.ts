import { Segment, SegmentRule } from 'common/types/responses'
import { AudienceSegment } from 'components/experiments/rollout'

// Copying a split re-salts it against the rollout segment, so it would match a
// different set of identities than the source segment does elsewhere. The
// server rejects these; the picker hides them so the choice never dead-ends.
const containsPercentageSplit = (rules: SegmentRule[]): boolean =>
  rules.some(
    (rule) =>
      rule.conditions?.some(
        (condition) => condition.operator === 'PERCENTAGE_SPLIT',
      ) || containsPercentageSplit(rule.rules ?? []),
  )

// The segments list already excludes system segments, so the remaining server
// rules the picker can enforce itself are these. Anything left over (a cohort
// pending deletion racing the request, say) still fails server-side, and the
// caller surfaces that message.
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
