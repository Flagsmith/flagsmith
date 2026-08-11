export type ParsedCsv = {
  columns: string[]
  rows: string[][]
}

export type ExtractedIdentifiers = {
  duplicateCount: number
  emptyCount: number
  identifiers: string[]
}

export function parseCsvText(text: string): string[][] {
  const rows: string[][] = []
  let row: string[] = []
  let field = ''
  let inQuotes = false
  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    if (inQuotes) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"'
          i++
        } else {
          inQuotes = false
        }
      } else {
        field += char
      }
    } else if (char === '"') {
      inQuotes = true
    } else if (char === ',') {
      row.push(field)
      field = ''
    } else if (char === '\n' || char === '\r') {
      if (char === '\r' && text[i + 1] === '\n') {
        i++
      }
      row.push(field)
      rows.push(row)
      row = []
      field = ''
    } else {
      field += char
    }
  }
  if (field !== '' || row.length) {
    row.push(field)
    rows.push(row)
  }
  return rows.filter((cells) => cells.some((cell) => cell.trim() !== ''))
}

export function toParsedCsv(
  rawRows: string[][],
  hasHeaders: boolean,
): ParsedCsv {
  if (!rawRows.length) {
    return { columns: [], rows: [] }
  }
  const columnCount = Math.max(...rawRows.map((cells) => cells.length))
  if (hasHeaders) {
    const [header, ...rows] = rawRows
    return {
      columns: Array.from(
        { length: columnCount },
        (_, i) => header[i]?.trim() || `Column ${i + 1}`,
      ),
      rows,
    }
  }
  return {
    columns: Array.from({ length: columnCount }, (_, i) => `Column ${i + 1}`),
    rows: rawRows,
  }
}

export function extractIdentifiers(
  rows: string[][],
  columnIndex: number,
): ExtractedIdentifiers {
  const seen = new Set<string>()
  const identifiers: string[] = []
  let emptyCount = 0
  let duplicateCount = 0
  for (const cells of rows) {
    const value = (cells[columnIndex] ?? '').trim()
    if (!value) {
      emptyCount++
    } else if (seen.has(value)) {
      duplicateCount++
    } else {
      seen.add(value)
      identifiers.push(value)
    }
  }
  return { duplicateCount, emptyCount, identifiers }
}
