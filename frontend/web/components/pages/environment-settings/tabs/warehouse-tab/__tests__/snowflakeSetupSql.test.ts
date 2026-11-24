import fs from 'fs'
import path from 'path'
import { getSnowflakeSetupSql } from 'components/pages/environment-settings/tabs/warehouse-tab/snowflakeSetupSql'

const getEventsColumns = (sql: string) =>
  sql
    .match(/CREATE TABLE IF NOT EXISTS \S+ \(([\s\S]*?)\);/)?.[1]
    .replace(/\s+/g, ' ')
    .trim()

describe('getSnowflakeSetupSql', () => {
  it.each([
    ['no values are given', undefined],
    [
      'values are blank',
      { database: ' ', role: '', schema: '  ', user: '', warehouse: ' ' },
    ],
  ])('uses the defaults when %s', (_, params) => {
    const sql = getSnowflakeSetupSql(params)

    expect(sql).toContain('CREATE WAREHOUSE IF NOT EXISTS FLAGSMITH_WH\n')
    expect(sql).toContain(
      'CREATE TABLE IF NOT EXISTS FLAGSMITH.FLAGSMITH_EXP.EVENTS (',
    )
    expect(sql).toContain(
      'GRANT SELECT, INSERT ON TABLE FLAGSMITH.FLAGSMITH_EXP.EVENTS TO ROLE FLAGSMITH_ROLE;',
    )
    expect(sql).toContain(
      'GRANT ROLE FLAGSMITH_ROLE TO USER FLAGSMITH_SERVICE;',
    )
  })

  it('templates the warehouse, database, schema, role and user', () => {
    const sql = getSnowflakeSetupSql({
      database: 'ANALYTICS',
      role: 'EXP_ROLE',
      schema: 'EXPERIMENTS',
      user: 'EXP_USER',
      warehouse: 'EXP_WH',
    })

    expect(sql).toContain('CREATE SCHEMA IF NOT EXISTS ANALYTICS.EXPERIMENTS;')
    expect(sql).toContain('GRANT USAGE ON WAREHOUSE EXP_WH TO ROLE EXP_ROLE;')
    expect(sql).toContain(
      'GRANT SELECT, INSERT ON TABLE ANALYTICS.EXPERIMENTS.EVENTS TO ROLE EXP_ROLE;',
    )
    expect(sql).toContain('CREATE USER IF NOT EXISTS EXP_USER\n')
    expect(sql).toContain(
      '  DEFAULT_ROLE = EXP_ROLE\n  DEFAULT_WAREHOUSE = EXP_WH\n',
    )
    expect(sql).toContain("RSA_PUBLIC_KEY = '<PUBLIC_KEY>';")
    expect(sql).not.toMatch(/FLAGSMITH/)
  })

  it('matches the events columns in experimentation/snowflake/events.sql', () => {
    const eventsSql = fs.readFileSync(
      path.join(
        __dirname,
        '../../../../../../../../experimentation/snowflake/events.sql',
      ),
      'utf8',
    )

    const columns = getEventsColumns(eventsSql)

    expect(columns).toContain('ENVIRONMENT_KEY STRING NOT NULL')
    expect(getEventsColumns(getSnowflakeSetupSql())).toEqual(columns)
  })
})
