import fs from 'fs'
import path from 'path'
import {
  getPostgresOnboardingSql,
  getPostgresSetupSql,
} from 'components/pages/environment-settings/tabs/warehouse-tab/postgresSetupSql'

const stripCommentsAndWhitespace = (sql: string) =>
  sql.replace(/--.*$/gm, '').replace(/\s+/g, ' ').trim()

describe('getPostgresOnboardingSql', () => {
  it('creates the table, then the user, then grants access', () => {
    const sql = getPostgresOnboardingSql()
    const positions = [
      'CREATE TABLE IF NOT EXISTS flagsmith_exp.events',
      "CREATE USER <USER> PASSWORD '<YOUR_PASSWORD>';",
      'GRANT USAGE ON SCHEMA flagsmith_exp TO <USER>;',
      'GRANT SELECT, INSERT ON flagsmith_exp.events TO <USER>;',
    ].map((statement) => sql.indexOf(statement))

    expect(positions[0]).toBeGreaterThan(-1)
    expect(positions).toEqual([...positions].sort((a, b) => a - b))
  })
})

describe('getPostgresSetupSql', () => {
  it('matches experimentation/postgres/events.sql', () => {
    const eventsSql = fs.readFileSync(
      path.join(
        __dirname,
        '../../../../../../../../experimentation/postgres/events.sql',
      ),
      'utf8',
    )

    expect(
      stripCommentsAndWhitespace(getPostgresSetupSql('flagsmith_exp')),
    ).toEqual(stripCommentsAndWhitespace(eventsSql))
  })
})
