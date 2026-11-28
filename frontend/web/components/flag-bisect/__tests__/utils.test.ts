import {
  culpritNames,
  errorDetail,
  headline,
  describeChange,
  describeValue,
  pendingGate,
  percent,
  stateLabel,
  stateTone,
} from 'components/flag-bisect/utils'
import { FlagBisectIncident } from 'common/types/responses'

const suspect = (feature: number, name: string) => ({
  after_enabled: true,
  after_value: null,
  before_enabled: false,
  before_value: null,
  changed_at: '2026-11-26T10:00:00Z',
  feature,
  feature_name: name,
  id: feature,
  posterior: 0,
  prior: 0,
})

describe('flag bisect utils', () => {
  it('maps states to tones and readable labels', () => {
    expect(stateTone('RESOLVED')).toBe('success')
    expect(stateTone('AWAITING_APPROVAL')).toBe('warning')
    expect(stateTone('NOT_A_FLAG_CHANGE')).toBe('info')
    expect(stateTone('PROBING')).toBe('danger')
    expect(stateLabel('NOT_A_FLAG_CHANGE')).toBe('Not a flag change')
  })

  it('describes values and changes', () => {
    expect(describeValue(false, 'x')).toBe('off')
    expect(describeValue(true, null)).toBe('on')
    expect(describeValue(true, 'hybrid_v2')).toBe('on (hybrid_v2)')
    expect(describeChange(suspect(1, 'a'))).toBe('off → on')
    expect(percent(0.0863)).toBe('8.6%')
  })

  it('names the culprits from the conclusion', () => {
    const incident: FlagBisectIncident = {
      baseline_rate: 0.01,
      canary_percent: 5,
      canary_segment: null,
      conclusion: { confidence: 0.99, ids: ['2'] },
      confirmed: true,
      created_at: '2026-11-26T10:00:00Z',
      envelope_approved_at: null,
      hypotheses: [],
      id: 1,
      max_minutes: 45,
      max_rounds: 12,
      messages: [],
      onset_at: '2026-11-26T10:00:00Z',
      probes: [],
      regression_rate: 0.09,
      remediation_result: null,
      rounds: 3,
      state: 'IDENTIFIED',
      suspects: [suspect(1, 'fast_checkout'), suspect(2, 'new_tax_engine')],
      updated_at: '2026-11-26T10:00:00Z',
    }
    expect(culpritNames(incident)).toEqual(['new_tax_engine'])
  })

  it('writes the headline and reads API errors', () => {
    const incident: FlagBisectIncident = {
      baseline_rate: 0.01,
      canary_percent: 5,
      canary_segment: null,
      conclusion: null,
      confirmed: false,
      created_at: '2026-11-26T10:00:00Z',
      envelope_approved_at: null,
      hypotheses: [],
      id: 2,
      max_minutes: 45,
      max_rounds: 12,
      messages: [],
      onset_at: '2026-11-26T10:00:00Z',
      probes: [],
      regression_rate: 0.09,
      remediation_result: null,
      rounds: 0,
      state: 'PROBING',
      suspects: [],
      updated_at: '2026-11-26T10:00:00Z',
    }
    expect(headline(incident)).toBe('Failure rate 1.0% → 9.0%')
    expect(headline({ ...incident, state: 'NOT_A_FLAG_CHANGE' })).toBe(
      'None of these flag changes caused it',
    )
    expect(errorDetail({ data: { detail: 'Not allowed' } })).toBe('Not allowed')
    expect(errorDetail(new Error('x'))).toBe('The request failed.')
  })

  it('knows which human gate is pending', () => {
    expect(pendingGate('AWAITING_APPROVAL')).toBe('envelope')
    expect(pendingGate('IDENTIFIED')).toBe('propose')
    expect(pendingGate('REMEDIATION_PROPOSED')).toBe('approve')
    expect(pendingGate('PROBING')).toBeNull()
  })
})
