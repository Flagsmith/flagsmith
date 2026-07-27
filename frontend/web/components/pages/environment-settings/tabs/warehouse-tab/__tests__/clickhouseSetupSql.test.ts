import { CLICKHOUSE_DEFAULTS } from 'components/pages/environment-settings/tabs/warehouse-tab/clickhouseConfig'
import { getClickHouseSetupSql } from 'components/pages/environment-settings/tabs/warehouse-tab/clickhouseSetupSql'

describe('getClickHouseSetupSql', () => {
  it('interpolates the configured database into both statements', () => {
    const sql = getClickHouseSetupSql('analytics')

    expect(sql).toContain('CREATE DATABASE IF NOT EXISTS analytics;')
    expect(sql).toContain('CREATE TABLE IF NOT EXISTS analytics.events')
    expect(sql).not.toContain('flagsmith_exp')
  })

  it('matches the form default database', () => {
    expect(getClickHouseSetupSql(CLICKHOUSE_DEFAULTS.database)).toContain(
      'CREATE TABLE IF NOT EXISTS flagsmith_exp.events',
    )
  })
})
