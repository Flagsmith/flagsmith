import { Segment, SegmentCohort, SegmentRule } from 'common/types/responses'
import { AudienceSegment } from 'components/experiments/rollout'
import { isSelectableAudienceSegment } from 'components/experiments/AudiencePicker/utils'

const ENVIRONMENT_ID = 'env-key'

const cohort = (environmentApiKey: string): SegmentCohort =>
  ({ environment_api_key: environmentApiKey } as SegmentCohort)

const rule = (operator: string, nested: SegmentRule[] = []): SegmentRule =>
  ({
    conditions: [{ operator, property: '', value: null }],
    rules: nested,
  } as SegmentRule)

const segment = (over: Partial<Segment>): Segment =>
  ({ id: 1, name: 'S1', rules: [rule('EQUAL')], ...over } as Segment)

const selected = (id: number): AudienceSegment => ({ id, name: `S${id}` })

describe('isSelectableAudienceSegment', () => {
  it.each([
    ['a plain segment', segment({}), [], true],
    ['an already-selected segment', segment({}), [selected(1)], false],
    ['a feature-specific segment', segment({ feature: 7 }), [], false],
    [
      'a cohort from this environment',
      segment({ cohort: cohort(ENVIRONMENT_ID) }),
      [],
      true,
    ],
    [
      'a cohort from another environment',
      segment({ cohort: cohort('other-env-key') }),
      [],
      false,
    ],
    [
      'a segment split at the top level',
      segment({ rules: [rule('PERCENTAGE_SPLIT')] }),
      [],
      false,
    ],
    [
      'a segment split in a nested rule',
      segment({ rules: [rule('EQUAL', [rule('PERCENTAGE_SPLIT')])] }),
      [],
      false,
    ],
    ['a segment with no rules', segment({ rules: [] }), [], false],
  ])('%s', (_, candidate, selection, expected) => {
    expect(
      isSelectableAudienceSegment(candidate, ENVIRONMENT_ID, selection),
    ).toBe(expected)
  })
})
