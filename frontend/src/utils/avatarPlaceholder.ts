/** 本地 SVG data URL，避免 picsum 等外网头像阻塞首屏 */

export function getAvatarPlaceholderDataUrl(seed: number, size: 40 | 48 = 40): string {
  const hue = Math.abs(seed) % 360
  const s = size
  const cx = s / 2
  const cy = s / 2
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 ${s} ${s}"><circle cx="${cx}" cy="${cy}" r="${cx}" fill="hsl(${hue} 28% 88%)"/><circle cx="${cx}" cy="${cy - s * 0.08}" r="${s * 0.22}" fill="#94a3b8"/><path d="M ${cx - s * 0.35} ${cy + s * 0.2} Q ${cx} ${cy + s * 0.42} ${cx + s * 0.35} ${cy + s * 0.2}" fill="#94a3b8"/></svg>`
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}
