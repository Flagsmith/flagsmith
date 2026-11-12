import { getAuditLogListView } from 'components/audit-log/AuditLogList/auditLogListView'

describe('getAuditLogListView', () => {
  it.each`
    name                                   | isLoading | itemCount    | view
    ${'first load'}                        | ${true}   | ${undefined} | ${'loading'}
    ${'new filters after an empty result'} | ${true}   | ${0}         | ${'loading'}
    ${'new filters after some rows'}       | ${true}   | ${3}         | ${'list'}
    ${'loaded with rows'}                  | ${false}  | ${3}         | ${'list'}
    ${'loaded with no rows'}               | ${false}  | ${0}         | ${'empty'}
    ${'skipped, nothing loaded'}           | ${false}  | ${undefined} | ${'empty'}
  `('$name: $view', ({ isLoading, itemCount, view }) => {
    expect(getAuditLogListView(isLoading, itemCount)).toBe(view)
  })
})
