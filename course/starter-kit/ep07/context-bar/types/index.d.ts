export type Row = {
  name: string
  tokens: number
  color: string
  kind: 'used' | 'free' | 'buffer'
}

export type Snapshot = { rows: Row[]; used: number; window: number }

declare module 'claude-code' {
  interface PluginState {
    'context-bar': { isShown: boolean; snapshot: Snapshot | null }
  }
}
