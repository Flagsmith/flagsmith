import {
  renderSummary,
  summariseReport,
  VisualReport,
} from '../visual-regression-summary'

// Shapes and messages copied from a real compare run's JSON report.
const changedResult = {
  attachments: [
    { name: 'flag-tests-pw-ts--features-list-expected.png' },
    { name: 'flag-tests-pw-ts--features-list-actual.png' },
    { name: 'flag-tests-pw-ts--features-list-diff.png' },
  ],
  error: {
    message:
      'Error: \u001b[2mexpect(\u001b[22mBuffer).toMatchSnapshot(expected) failed\n\n  1,204 pixels (ratio 0.32 of all image pixels) are different.',
  },
  status: 'failed',
}
const newResult = {
  attachments: [
    { name: 'project-test-pw-ts--new-project-expected.png' },
    { name: 'project-test-pw-ts--new-project-actual.png' },
  ],
  error: { message: "Error: A snapshot doesn't exist at …, writing actual." },
  status: 'failed',
}
const passedResult = { attachments: [], status: 'passed' }

const report: VisualReport = {
  suites: [
    {
      suites: [
        {
          specs: [
            {
              tests: [{ results: [changedResult] }],
              title: 'flag-tests.pw.ts / features list',
            },
            {
              tests: [{ results: [newResult] }],
              title: 'project-test.pw.ts / new project',
            },
            {
              tests: [{ results: [passedResult] }],
              title: 'sso-test.pw.ts / scim empty',
            },
          ],
        },
      ],
    },
  ],
}

describe('summariseReport', () => {
  it('summariseReport__mixed_results__lists_changed_and_new_screenshots', () => {
    // Given / When
    const summary = summariseReport(report)

    // Then
    expect(summary).toEqual({
      changes: [
        {
          isNew: false,
          pixels: 1204,
          ratio: 0.32,
          title: 'flag-tests.pw.ts / features list',
        },
        {
          isNew: true,
          pixels: undefined,
          ratio: undefined,
          title: 'project-test.pw.ts / new project',
        },
      ],
      total: 3,
    })
  })
})

describe('renderSummary', () => {
  it('renderSummary__no_changes__says_nothing_changed', () => {
    // Given / When
    const markdown = renderSummary({ changes: [], total: 26 })

    // Then
    expect(markdown).toBe('No visual changes in 26 screenshots.')
  })

  it('renderSummary__changes__renders_a_table_of_them', () => {
    // Given / When
    const markdown = renderSummary(summariseReport(report))

    // Then
    expect(markdown).toBe(
      [
        '**1 changed, 1 new** of 3 screenshots',
        '',
        '| Screenshot | Change |',
        '| --- | --- |',
        '| flag-tests.pw.ts / features list | 1,204 px differ (0.32) |',
        '| project-test.pw.ts / new project | New, no baseline |',
      ].join('\n'),
    )
  })
})
