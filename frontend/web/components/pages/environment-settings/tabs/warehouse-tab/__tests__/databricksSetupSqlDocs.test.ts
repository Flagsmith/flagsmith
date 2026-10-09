import fs from 'fs'
import path from 'path'
import { getDatabricksSetupSql } from 'components/pages/environment-settings/tabs/warehouse-tab/databricksSetupSql'

describe('getDatabricksSetupSql', () => {
  it('matches the copy of the script in the documentation', () => {
    const doc = fs.readFileSync(
      path.join(
        __dirname,
        '../../../../../../../../docs/docs/experimentation/connect-databricks.md',
      ),
      'utf8',
    )
    const fencedSql = doc.match(/```sql\n([\s\S]*?)```/)?.[1] ?? ''

    expect(fencedSql.trim()).toEqual(getDatabricksSetupSql())
  })
})
