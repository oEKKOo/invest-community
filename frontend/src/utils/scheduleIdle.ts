/** Defer work until the browser is idle (improves first paint / TTI). Falls back to macrotask queue. */
export function scheduleIdle(fn: () => void, timeout = 2000): void {
  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    ;(window as Window & { requestIdleCallback: (cb: () => void, opts?: { timeout?: number }) => number }).requestIdleCallback(
      fn,
      { timeout }
    )
  } else {
    setTimeout(fn, 0)
  }
}
