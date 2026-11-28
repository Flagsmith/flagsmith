import 'react'

declare module 'react' {
  interface CSSProperties {
    /** Width of a Flag Bisect meter's fill, e.g. `42%`. */
    '--flag-bisect-fill'?: string
  }
}
