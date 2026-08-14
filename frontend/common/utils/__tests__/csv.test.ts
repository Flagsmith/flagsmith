import {
  extractIdentifiers,
  parseCsvText,
  toCsvColumn,
  toParsedCsv,
} from 'common/utils/csv'

describe('parseCsvText', () => {
  const cases: [string, string, string[][]][] = [
    ['single column', 'a\nb\nc', [['a'], ['b'], ['c']]],
    [
      'multiple columns',
      'id,email\n1,a@b.com',
      [
        ['id', 'email'],
        ['1', 'a@b.com'],
      ],
    ],
    ['crlf line endings', 'a\r\nb\r\n', [['a'], ['b']]],
    [
      'quoted fields with commas and escaped quotes',
      '"a,b","say ""hi"""\nc,d',
      [
        ['a,b', 'say "hi"'],
        ['c', 'd'],
      ],
    ],
    ['blank lines dropped', 'a\n\n \nb', [['a'], ['b']]],
    ['empty input', '', []],
  ]

  test.each(cases)('%s', (_, input, expected) => {
    expect(parseCsvText(input)).toEqual(expected)
  })
})

describe('toParsedCsv', () => {
  const rawRows = [
    ['id', 'email'],
    ['1', 'a@b.com'],
  ]

  test('with headers, first row becomes column names', () => {
    expect(toParsedCsv(rawRows, true)).toEqual({
      columns: ['id', 'email'],
      rows: [['1', 'a@b.com']],
    })
  })

  test('without headers, generates Column N names', () => {
    expect(toParsedCsv(rawRows, false)).toEqual({
      columns: ['Column 1', 'Column 2'],
      rows: rawRows,
    })
  })

  test('blank header cells fall back to Column N', () => {
    expect(toParsedCsv([['id', ''], ['1']], true).columns).toEqual([
      'id',
      'Column 2',
    ])
  })

  test('empty input yields no columns or rows', () => {
    expect(toParsedCsv([], true)).toEqual({ columns: [], rows: [] })
  })
})

describe('extractIdentifiers', () => {
  test('trims values and counts empty and duplicate rows', () => {
    const rows = [['a'], [' b '], [''], ['a'], ['  '], ['b']]
    expect(extractIdentifiers(rows, 0)).toEqual({
      duplicateCount: 2,
      emptyCount: 2,
      identifiers: ['a', 'b'],
    })
  })

  test('missing cells in short rows count as empty', () => {
    expect(extractIdentifiers([['x', 'y'], ['z']], 1)).toEqual({
      duplicateCount: 0,
      emptyCount: 1,
      identifiers: ['y'],
    })
  })
})

describe('toCsvColumn', () => {
  test.each([
    ['plain values', ['a', 'b'], 'a\nb'],
    ['comma quoted', ['Doe, Jane', 'b'], '"Doe, Jane"\nb'],
    ['quote escaped', ['say "hi"'], '"say ""hi"""'],
    ['newline quoted', ['line1\nline2'], '"line1\nline2"'],
  ])('%s', (_, values, expected) => {
    expect(toCsvColumn(values)).toEqual(expected)
  })

  test('round-trips through parseCsvText', () => {
    const values = ['plain', 'Doe, Jane', 'say "hi"', 'multi\nline']
    expect(parseCsvText(toCsvColumn(values)).map((row) => row[0])).toEqual(
      values,
    )
  })
})
