import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Row, Snapshot } from '../types'
import { allot, compact } from './layout'

const isShown = atom({ plugin: 'context-bar', key: 'isShown' } as const, true)
const snapshot = atom({ plugin: 'context-bar', key: 'snapshot' } as const, null)

const GLYPH = { used: '█', buffer: '▒', free: '░' } as const
const MAX_COLUMNS = 100

const refresh = async ($: EngineInterface) => {
  try {
    // `summary` estimates locally; `full` would send a token-count request per tool each turn.
    const { context } = await $.session.usage({ breakdown: 'summary' })
    const breakdown = context.breakdown

    if (!breakdown) {
      return
    }

    const rows: Row[] = []

    for (const row of breakdown.categories) {
      if (row.kind !== 'deferred' && row.tokens > 0) {
        rows.push({ name: row.name, tokens: row.tokens, color: row.color, kind: row.kind })
      }
    }

    const next: Snapshot = {
      rows,
      used: breakdown.totalTokens,
      window: breakdown.rawMaxTokens,
    }
    await update($, snapshot, () => next)
  } catch {
    // No session bound yet: the bar keeps what it last drew.
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'context-bar',
      description: 'Toggle the context window bar above the prompt',
    })
    const started = await next(e)
    await refresh($)

    return started
  })

  on('command.run', { command: 'context-bar' }, async $ => {
    const now = !(await read($, isShown))
    await update($, isShown, () => now)

    if (now) {
      await refresh($)
    }

    return { text: now ? 'Context bar shown.' : 'Context bar hidden.' }
  })

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    await refresh($)

    return done
  })

  on('session.compact', async ($, e, next) => {
    const done = await next(e)
    await refresh($)

    return done
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const shot = await read($, snapshot)

    if (e.props.hasSurvey || shot === null || !(await read($, isShown))) {
      return next(e)
    }

    const columns = Math.min(e.props.bodyColumns, MAX_COLUMNS)
    const cells = allot(shot.rows, columns)

    if (cells.every(n => n === 0)) {
      return next(e)
    }

    const { Box, Text } = $.ui.resolve(e)
    const percent = shot.window > 0 ? Math.round((shot.used / shot.window) * 100) : 0

    return (
      <Box flexDirection="column">
        <Text wrap="truncate-end">
          {shot.rows.map((row, i) => (
            <Text color={row.color}>
              {GLYPH[row.kind].repeat(cells[i] ?? 0)}
            </Text>
          ))}
        </Text>
        <Text wrap="wrap">
          <Text weight="bold">
            {compact(shot.used)}/{compact(shot.window)} ({percent}%)
          </Text>
          {shot.rows.map(row => (
            <Text>
              {'  '}
              <Text color={row.color}>{GLYPH[row.kind]}</Text>
              <Text dimColor>
                {' '}
                {row.name} {compact(row.tokens)}
              </Text>
            </Text>
          ))}
        </Text>
      </Box>
    )
  })
}
