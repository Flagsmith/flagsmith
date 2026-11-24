import fs from 'fs'
import path from 'path'
import { getSnowflakeSetupSql } from 'components/pages/environment-settings/tabs/warehouse-tab/snowflakeSetupSql'

const normalise = (sql: string) => sql.replace(/\s+/g, ' ').trim()

describe('getSnowflakeSetupSql', () => {
  it('matches the copy of the script in the documentation', () => {
    const doc = fs.readFileSync(
      path.join(
        __dirname,
        '../../../../../../../../docs/docs/experimentation/connect-a-warehouse/snowflake.md',
      ),
      'utf8',
    )
    const fencedSql =
      doc.match(
        /```sql\n(-- Create the role, warehouse, database, schema and events table\n[\s\S]*?)```/,
      )?.[1] ?? ''

    expect(normalise(fencedSql)).toEqual(normalise(getSnowflakeSetupSql()))
  })
})
