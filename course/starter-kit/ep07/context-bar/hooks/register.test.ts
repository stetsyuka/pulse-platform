import { expect, test } from 'claude-code/testing'

import { allot, compact } from './layout'

const CATEGORIES = [
  { name: 'System prompt', tokens: 10_000, color: 'promptBorder', isDeferred: false, kind: 'used' },
  { name: 'Messages', tokens: 40_000, color: 'claude', isDeferred: false, kind: 'used' },
  { name: 'MCP tools (deferred)', tokens: 30_000, color: 'inactive', isDeferred: true, kind: 'deferred' },
  { name: 'Free space', tokens: 130_000, color: 'subtle', isDeferred: false, kind: 'free' },
  { name: 'Autocompact buffer', tokens: 20_000, color: 'warning', isDeferred: false, kind: 'buffer' },
]

const USAGE = {
  startedAt: 0,
  context: {
    tokens: 50_000,
    window: 200_000,
    percent: 25,
    breakdown: { categories: CATEGORIES, totalTokens: 50_000, rawMaxTokens: 200_000 },
  },
}

const RUN = {
  command: 'context-bar',
  args: '',
  origin: { kind: 'human' },
  presentation: { isFullscreen: false },
} as never

const PROPS = { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 40 }

test('allot fills the width exactly and never hides a non-empty row', () => {
  const rows = [
    { name: 'a', tokens: 1, color: 'x', kind: 'used' as const },
    { name: 'b', tokens: 9999, color: 'x', kind: 'used' as const },
    { name: 'c', tokens: 0, color: 'x', kind: 'free' as const },
  ]
  const cells = allot(rows, 20)

  expect(cells.reduce((sum, n) => sum + n, 0)).toBe(20)
  expect(cells[0]).toBe(1)
  expect(cells[2]).toBe(0)
  expect(compact(1234)).toBe('1.2k')
  expect(compact(200_000)).toBe('200k')
})

for (const surface of ['terminal', 'desktop'] as const) {
  test(`draws one colored segment per category on ${surface}, toggled by /context-bar`, async ($, on) => {
    on('session.usage', () => ({ value: USAGE }) as never)

    // Off, then on again: turning it on reads the breakdown.
    expect(await $.command.run(RUN)).toMatchObject({ text: 'Context bar hidden.' })
    expect(await $.command.run(RUN)).toMatchObject({ text: 'Context bar shown.' })

    const ui = await $.ui.mount({
      plugin: 'context-bar',
      surface,
      component: 'AbovePrompt',
      props: PROPS as never,
    })

    type Node = { props?: { color?: string }; children: (Node | string)[] }
    const drawn = (await ui.drawn()) as unknown as Node
    const bar = drawn.children[0] as Node
    const legend = drawn.children[1] as Node
    const segments = bar.children as Node[]

    // The deferred row is left out; the rest share the 40 cells by tokens.
    expect(segments.map(one => one.props?.color)).toEqual(['promptBorder', 'claude', 'subtle', 'warning'])
    expect(segments.map(one => String(one.children[0]).length)).toEqual([2, 8, 26, 4])
    expect((legend.children[0] as Node).children.join('')).toBe('50k/200k (25%)')
    expect(await ui.find({ text: /deferred/ })).toBeUndefined()

    await ui.unmount()
    await $.command.run(RUN)

    // Hidden, the mod passes to the engine; nothing sits beneath it here, so the mount rejects.
    const hidden = await $.ui
      .mount({ plugin: 'context-bar', surface, component: 'AbovePrompt', props: PROPS as never })
      .catch(() => undefined)

    expect(await hidden?.find({ text: /200k/ })).toBeUndefined()
  })
}
