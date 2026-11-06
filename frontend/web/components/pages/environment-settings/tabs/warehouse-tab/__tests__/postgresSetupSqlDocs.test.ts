import fs from 'fs'
import path from 'path'
import { getPostgresOnboardingSql } from 'components/pages/environment-settings/tabs/warehouse-tab/postgresSetupSql'

const normalise = (sql: string) => sql.replace(/\s+/g, ' ').trim()

describe('getPostgresOnboardingSql', () => {
  it('matches the copy of the script in the documentation', () => {
    const doc = fs.readFileSync(
      path.join(
        __dirname,
        '../../../../../../../../docs/docs/experimentation/connect-postgresql.md',
      ),
      'utf8',
    )
    const fencedSql =
      doc.match(
        /```sql\n(-- Create the schema and events table\n[\s\S]*?)```/,
      )?.[1] ?? ''

    expect(normalise(fencedSql)).toEqual(normalise(getPostgresOnboardingSql()))
  })
})
