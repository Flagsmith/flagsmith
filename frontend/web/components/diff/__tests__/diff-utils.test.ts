import { Segment } from 'common/types/responses'
import {
  DIFF_SEGMENT_MODES,
  getSegmentDiffPair,
} from 'components/diff/diff-utils'

jest.mock('common/utils/utils', () => ({}))

const makeSegment = (id: number, name: string): Segment => ({
  description: `${name} description`,
  id,
  metadata: [],
  name,
  project: 1,
  rules: [],
  uuid: `segment-${id}`,
})

describe('getSegmentDiffPair', () => {
  it('returns [oldSegment, newSegment] in Diff mode', () => {
    const oldSegment = makeSegment(1, 'Old')
    const newSegment = makeSegment(1, 'New')

    expect(
      getSegmentDiffPair(DIFF_SEGMENT_MODES.Diff, oldSegment, newSegment),
    ).toEqual([oldSegment, newSegment])
  })

  it('returns [newSegment, newSegment] in New Value mode', () => {
    const oldSegment = makeSegment(1, 'Old')
    const newSegment = makeSegment(1, 'New')

    expect(
      getSegmentDiffPair(
        DIFF_SEGMENT_MODES['New Value'],
        oldSegment,
        newSegment,
      ),
    ).toEqual([newSegment, newSegment])
  })

  it('returns [oldSegment, oldSegment] in Old Value mode', () => {
    const oldSegment = makeSegment(1, 'Old')
    const newSegment = makeSegment(1, 'New')

    expect(
      getSegmentDiffPair(
        DIFF_SEGMENT_MODES['Old Value'],
        oldSegment,
        newSegment,
      ),
    ).toEqual([oldSegment, oldSegment])
  })

  it('reflects updated segment references without stale state', () => {
    const initialOld = makeSegment(1, 'Old v1')
    const initialNew = makeSegment(1, 'New v1')
    const updatedOld = makeSegment(1, 'Old v2')
    const updatedNew = makeSegment(1, 'New v2')

    expect(
      getSegmentDiffPair(DIFF_SEGMENT_MODES.Diff, initialOld, initialNew),
    ).toEqual([initialOld, initialNew])
    expect(
      getSegmentDiffPair(DIFF_SEGMENT_MODES.Diff, updatedOld, updatedNew),
    ).toEqual([updatedOld, updatedNew])
  })
})
