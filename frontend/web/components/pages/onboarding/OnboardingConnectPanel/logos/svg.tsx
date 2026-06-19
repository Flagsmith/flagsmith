import React, { FC, ReactNode } from 'react'
import Utils from 'common/utils/utils'

export type LogoProps = {
  // Brand colour baked into each logo. Near-black marks (luminosity < 0.06,
  // e.g. Next.js / Rust / iOS) fall back to currentColor so they stay visible
  // on the dark chip, where the surrounding text colour is light.
  color?: string
  children: ReactNode
}

// Shared wrapper for the SDK brand logos: a 24×24 single-path mark rendered at
// 16px, decorative (aria-hidden). One logo component per file imports this -
// see ./index.ts. Mirrors the icon convention we're standardising on.
const Svg: FC<LogoProps> = ({ children, color }) => {
  const fill =
    color && Utils.colour(color).luminosity() < 0.06 ? 'currentColor' : color
  return (
    <svg viewBox='0 0 24 24' width={16} height={16} fill={fill} aria-hidden>
      {children}
    </svg>
  )
}

export default Svg
