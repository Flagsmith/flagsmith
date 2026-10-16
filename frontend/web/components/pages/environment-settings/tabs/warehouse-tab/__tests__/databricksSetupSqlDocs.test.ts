import fs from 'fs'
import path from 'path'
import { getDatabricksSetupSql } from 'components/pages/environment-settings/tabs/warehouse-tab/databricksSetupSql'

const normalise = (sql: string) => sql.replace(/\s+/g, ' ').trim()

describe('getDatabricksSetupSql', () => {
  it('matches the copy of the script in the documentation', () => {
    const doc = fs.readFileSync(
      path.join(
        __dirname,
        '../../../../../../../../docs/docs/experimentation/connect-databricks.md',
      ),
      'utf8',
    )
    const fencedSql =
      doc.match(
        /```sql\n(-- Create the schema and events table\n[\s\S]*?)```/,
      )?.[1] ?? ''

    expect(normalise(fencedSql)).toEqual(normalise(getDatabricksSetupSql()))
  })
})
