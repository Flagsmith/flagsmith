import fs from 'fs'
import path from 'path'
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

    expect(sql).toContain(
      "CREATE USER IF NOT EXISTS <USERNAME> IDENTIFIED BY '<YOUR_SECURED_PASSWORD>';",
    )
    expect(sql).toContain(
      'GRANT INSERT, SELECT ON flagsmith_exp.* TO <USERNAME>;',
    )
    expect(sql).toContain(getClickHouseSetupSql('flagsmith_exp'))
  })

  it('matches the copy of the script in the documentation', () => {
    const doc = fs.readFileSync(
      path.join(
        __dirname,
        '../../../../../../../../docs/docs/experimentation/connect-a-warehouse.md',
      ),
      'utf8',
    )
    const fencedSql = doc.match(/```sql\n([\s\S]*?)```/)?.[1] ?? ''
    const dedented = fencedSql
      .split('\n')
      .map((line) => line.replace(/^ {3}/, ''))
      .join('\n')
      .trim()

    expect(dedented).toEqual(getClickHouseOnboardingSql())
  })
})
