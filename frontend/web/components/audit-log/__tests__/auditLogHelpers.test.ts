import moment from 'moment'
import { AuditLogItem } from 'common/types/responses'
import { groupAuditLogsByDay } from 'components/audit-log/groupAuditLogsByDay'
import { getAuditLogScopeLabel } from 'components/audit-log/auditLogScope'
import {
  getAuditLogTypeIcon,
  getAuditLogTypeLabel,
} from 'components/audit-log/auditLogType'

const project = { id: 1, name: 'Website' }
const environment = { name: 'Production' }

const log = (id: number, created_date: string): AuditLogItem => ({
  author: null,
  created_date,
  environment: null,
  id,
  is_system_event: false,
  log: `Log ${id}`,
  organisation: null,
  project: null,
  related_object_id: null,
  related_object_type: null,
  related_object_uuid: null,
})

describe('groupAuditLogsByDay', () => {
  const now = moment('2026-11-10T15:00:00')

  it('labels today and yesterday, and keeps the API order inside a day', () => {
    const days = groupAuditLogsByDay(
      [
        log(3, '2026-11-10T14:32:00'),
        log(2, '2026-11-10T09:00:00'),
        log(1, '2026-11-09T17:20:00'),
      ],
      now,
    )
    expect(days.map((d) => d.label)).toEqual([
      'Today · Tuesday 10 November',
      'Yesterday · Monday 9 November',
    ])
    expect(days[0].items.map((i) => i.id)).toEqual([3, 2])
  })

  it('adds the year only for another year', () => {
    const days = groupAuditLogsByDay(
      [log(2, '2026-11-01T10:00:00'), log(1, '2025-12-31T10:00:00')],
      now,
    )
    expect(days.map((d) => d.label)).toEqual([
      'Sunday 1 November',
      'Wednesday 31 December 2025',
    ])
  })

  it('returns no days for no logs', () => {
    expect(groupAuditLogsByDay([], now)).toEqual([])
  })
})

describe('getAuditLogScopeLabel', () => {
  it.each`
    hasProject | hasEnvironment | label
    ${false}   | ${false}       | ${'Organisation'}
    ${false}   | ${true}        | ${'Production'}
    ${true}    | ${false}       | ${'Website'}
    ${true}    | ${true}        | ${'Website · Production'}
  `(
    'project $hasProject, environment $hasEnvironment: $label',
    ({ hasEnvironment, hasProject, label }) => {
      expect(
        getAuditLogScopeLabel({
          environment: hasEnvironment ? environment : null,
          project: hasProject ? project : null,
        }),
      ).toBe(label)
    },
  )
})

describe('getAuditLogTypeIcon', () => {
  it.each`
    type                | hasProject | icon
    ${'FEATURE_STATE'}  | ${true}    | ${'features'}
    ${'SEGMENT'}        | ${true}    | ${'pie-chart'}
    ${'CHANGE_REQUEST'} | ${true}    | ${'request'}
    ${null}             | ${false}   | ${'people'}
    ${null}             | ${true}    | ${'list'}
  `('$type with project $hasProject: $icon', ({ hasProject, icon, type }) => {
    expect(
      getAuditLogTypeIcon({
        project: hasProject ? project : null,
        related_object_type: type,
      }),
    ).toBe(icon)
  })
})

describe('getAuditLogTypeLabel', () => {
  it.each`
    type               | hasProject | label
    ${'FEATURE_STATE'} | ${true}    | ${'Feature'}
    ${'EF_VERSION'}    | ${true}    | ${'Feature'}
    ${null}            | ${false}   | ${'Organisation'}
    ${null}            | ${true}    | ${'Project'}
  `('$type with project $hasProject: $label', ({ hasProject, label, type }) => {
    expect(
      getAuditLogTypeLabel({
        project: hasProject ? project : null,
        related_object_type: type,
      }),
    ).toBe(label)
  })
})
