import { getDatabricksSetupSql } from 'components/pages/environment-settings/tabs/warehouse-tab/databricksSetupSql'

describe('getDatabricksSetupSql', () => {
  it('uses placeholders and the default schema when no values are given', () => {
    const sql = getDatabricksSetupSql()

    expect(sql).toContain(
      'CREATE SCHEMA IF NOT EXISTS <CATALOG>.flagsmith_exp;',
    )
    expect(sql).toContain(
      'CREATE TABLE IF NOT EXISTS <CATALOG>.flagsmith_exp.events (',
    )
    expect(sql).toContain(
      'GRANT USE CATALOG ON CATALOG <CATALOG> TO `<CLIENT_ID>`;',
    )
    expect(sql).not.toContain('<SCHEMA>')
  })

  it('templates the catalog, schema and client ID', () => {
    const sql = getDatabricksSetupSql({
      catalog: 'workspace',
      clientId: 'abc-123',
      schema: 'experiments',
    })

    expect(sql).toContain('CREATE SCHEMA IF NOT EXISTS workspace.experiments;')
    expect(sql).toContain(
      'GRANT USE SCHEMA ON SCHEMA workspace.experiments TO `abc-123`;',
    )
    expect(sql).toContain(
      'GRANT SELECT, MODIFY ON TABLE workspace.experiments.events TO `abc-123`;',
    )
    expect(sql).not.toMatch(/<CATALOG>|<CLIENT_ID>/)
  })

  it('falls back to placeholders for blank values', () => {
    const sql = getDatabricksSetupSql({
      catalog: '  ',
      clientId: '',
      schema: ' ',
    })

    expect(sql).toContain(
      'GRANT SELECT, MODIFY ON TABLE <CATALOG>.flagsmith_exp.events TO `<CLIENT_ID>`;',
    )
  })

  it('clusters the events table', () => {
    expect(getDatabricksSetupSql()).toContain(
      'CLUSTER BY (environment_key, event, feature_name, timestamp);',
    )
  })
})
