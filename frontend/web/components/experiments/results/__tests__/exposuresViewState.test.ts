import {
  canRefreshExposures,
  deriveExposuresViewState,
} from 'components/experiments/results/exposuresViewState'
import { ExperimentExposures, ExperimentStatus } from 'common/types/responses'

const exposures = (
  over: Partial<ExperimentExposures> = {},
): ExperimentExposures => ({
  as_of: null,
  last_error_at: null,
  payload: null,
  refresh_requested_at: null,
  ...over,
})

const loaded = exposures({
  as_of: '2026-06-12T10:00:00Z',
  payload: {
    excluded_identities: 0,
    timeseries: { granularity: 'day', points: [] },
  },
})

describe('deriveExposuresViewState', () => {
  it('is empty when there is no payload and nothing in flight', () => {
    expect(deriveExposuresViewState(exposures()).kind).toBe('empty')
  })

  it('is loaded when a payload is present and fresh', () => {
    expect(deriveExposuresViewState(loaded).kind).toBe('loaded')
  })

  it('is refreshing when a request is newer than the last result', () => {
    const state = deriveExposuresViewState({
      ...loaded,
      refresh_requested_at: '2026-06-12T11:00:00Z',
    })
    expect(state.kind).toBe('refreshing')
  })

  it('is error when the last error is newer than as_of, preserving stale payload', () => {
    const state = deriveExposuresViewState({
      ...loaded,
      last_error_at: '2026-06-12T12:00:00Z',
    })
    expect(state).toEqual({ kind: 'error', staleAvailable: true })
  })

  it('prefers refreshing over a prior error', () => {
    const state = deriveExposuresViewState({
      ...loaded,
      last_error_at: '2026-06-12T12:00:00Z',
      refresh_requested_at: '2026-06-12T13:00:00Z',
    })
    expect(state.kind).toBe('refreshing')
  })
})

describe('canRefreshExposures', () => {
  const cases: [ExperimentStatus, boolean][] = [
    ['created', false],
    ['running', true],
    ['paused', true],
  ]
  cases.forEach(([status, can]) => {
    it(`${status} → canRefresh=${can}`, () => {
      expect(canRefreshExposures(status, loaded).canRefresh).toBe(can)
    })
  })
  it('blocks refresh once completed with a computed payload', () => {
    expect(canRefreshExposures('completed', loaded)).toEqual({
      canRefresh: false,
      reason: 'final',
    })
  })
})
