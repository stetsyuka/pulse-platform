import type { Row } from '../types'

/**
 * Splits `columns` cells among the rows in proportion to their tokens
 * (largest remainder), giving every non-empty row at least one cell.
 */
export const allot = (rows: readonly Row[], columns: number): number[] => {
  const total = rows.reduce((sum, row) => sum + row.tokens, 0)
  const live = rows.filter(row => row.tokens > 0).length

  if (total <= 0 || columns < live) {
    return rows.map(() => 0)
  }

  const exact = rows.map(row => (row.tokens / total) * columns)
  const cells = rows.map((row, i) =>
    row.tokens > 0 ? Math.max(1, Math.floor(exact[i] ?? 0)) : 0,
  )
  let spare = columns - cells.reduce((sum, n) => sum + n, 0)

  while (spare !== 0) {
    // Hand out (or take back) one cell at a time where the rounding error is largest.
    let pick = -1
    let best = -Infinity

    rows.forEach((row, i) => {
      const have = cells[i] ?? 0
      const want = exact[i] ?? 0
      const gap = spare > 0 ? want - have : have - want

      if (row.tokens > 0 && (spare > 0 || have > 1) && gap > best) {
        best = gap
        pick = i
      }
    })

    if (pick < 0) {
      break
    }

    cells[pick] = (cells[pick] ?? 0) + Math.sign(spare)
    spare -= Math.sign(spare)
  }

  return cells
}

export const compact = (tokens: number): string => {
  if (tokens >= 1_000_000) {
    return `${(tokens / 1_000_000).toFixed(1)}M`
  }

  if (tokens >= 1000) {
    return `${(tokens / 1000).toFixed(tokens >= 10_000 ? 0 : 1)}k`
  }

  return String(tokens)
}
