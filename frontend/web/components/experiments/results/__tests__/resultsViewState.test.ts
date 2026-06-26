import {
  canRefreshResults,
  deriveResultsViewState,
  getResultsRefreshLabel,
} from 'components/experiments/results/resultsViewState'
import {
  ExperimentBayesianResults,
  ExperimentStatus,
} from 'common/types/responses'

const results = (
  over: Partial<ExperimentBayesianResults> = {},
): ExperimentBayesianResults => ({
  as_of: null,
  is_final: false,
  last_error_at: null,
  payload: null,
  refresh_requested_at: null,
  ...over,
})

const loaded = results({
  as_of: '2026-06-12T10:00:00Z',
  payload: { metrics: [], srm_p_value: null },
})

describe('deriveResultsViewState', () => {
  it('is empty when there is no payload and nothing in flight', () => {
    expect(deriveResultsViewState(results()).kind).toBe('empty')
  })

  it('is loaded when a payload is present and fresh', () => {
    expect(deriveResultsViewState(loaded).kind).toBe('loaded')
  })

  it('is refreshing when a request is newer than the last result', () => {
    const state = deriveResultsViewState({
      ...loaded,
      refresh_requested_at: '2026-06-12T11:00:00Z',
    })
    expect(state.kind).toBe('refreshing')
  })

  it('is error when the last error is newer than as_of, preserving stale payload', () => {
    const state = deriveResultsViewState({
      ...loaded,
      last_error_at: '2026-06-12T12:00:00Z',
    })
    expect(state).toEqual({ kind: 'error', staleAvailable: true })
  })

  it('prefers refreshing over a prior error', () => {
    const state = deriveResultsViewState({
      ...loaded,
      last_error_at: '2026-06-12T12:00:00Z',
      refresh_requested_at: '2026-06-12T13:00:00Z',
    })
    expect(state.kind).toBe('refreshing')
  })
})

describe('canRefreshResults', () => {
  const cases: [ExperimentStatus, boolean][] = [
    ['created', false],
    ['running', true],
    ['paused', true],
    ['completed', true],
  ]
  cases.forEach(([status, can]) => {
    it(`${status} → canRefresh=${can}`, () => {
      expect(canRefreshResults(status, loaded).canRefresh).toBe(can)
    })
  })

  it('blocks refresh once the results are final', () => {
    expect(canRefreshResults('running', { ...loaded, is_final: true })).toEqual(
      {
        canRefresh: false,
        reason: 'final',
      },
    )
  })
})

describe('getResultsRefreshLabel', () => {
  it('prefers a retry countdown over everything else', () => {
    expect(
      getResultsRefreshLabel(90, true, { kind: 'error', staleAvailable: true }),
    ).toEqual({ message: 'Computing… retry in 1m 30s', tone: 'muted' })
  })

  it('shows an in-progress message while refreshing', () => {
    expect(getResultsRefreshLabel(null, true, { kind: 'loaded' })).toEqual({
      message: 'Computing… results will update automatically.',
      tone: 'muted',
    })
  })

  it('surfaces a danger message on error when idle', () => {
    expect(
      getResultsRefreshLabel(null, false, {
        kind: 'error',
        staleAvailable: false,
      }),
    ).toEqual({
      message: 'The last results computation failed.',
      tone: 'danger',
    })
  })

  it('is null when idle and healthy', () => {
    expect(getResultsRefreshLabel(null, false, { kind: 'loaded' })).toBeNull()
  })
})
