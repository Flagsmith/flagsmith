import { CLICKHOUSE_DEFAULTS } from 'components/pages/environment-settings/tabs/warehouse-tab/clickhouseConfig'
import {
  getClickHouseOnboardingSql,
  getClickHouseSetupSql,
} from 'components/pages/environment-settings/tabs/warehouse-tab/clickhouseSetupSql'

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

describe('getClickHouseOnboardingSql', () => {
  it('creates a placeholder user, grants it access, and includes the DDL', () => {
    const sql = getClickHouseOnboardingSql()

    expect(sql).toContain('CREATE USER IF NOT EXISTS <USER>')
    expect(sql).toContain(
      "IDENTIFIED WITH sha256_password BY '<CHANGE_ME_PASSWORD>';",
    )
    expect(sql).toContain(
      'GRANT SELECT, INSERT ON flagsmith_exp.events TO <USER>;',
    )
    expect(sql).toContain(
      'GRANT SHOW TABLES, SHOW COLUMNS ON flagsmith_exp.* TO <USER>;',
    )
    expect(sql).toContain(getClickHouseSetupSql('flagsmith_exp'))
  })

  it('creates the events table before the user and grants that reference it', () => {
    const sql = getClickHouseOnboardingSql()
    const createTable = sql.indexOf('CREATE TABLE')

    expect(createTable).toBeLessThan(sql.indexOf('CREATE USER'))
    expect(createTable).toBeLessThan(sql.indexOf('GRANT'))
  })
})
