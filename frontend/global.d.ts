import { Component, FC, ReactNode } from 'react'
import _Select from './web/components/Select'
export type OpenConfirm = {
  title: ReactNode
  body: ReactNode
  onYes: () => void
  onNo?: () => void
  destructive?: boolean
  yesText?: string
  noText?: string
}
import { TooltipProps } from './web/components/Tooltip'
export declare const openModal: (name?: string) => Promise<void>
declare global {
  const openModal: (
    title: ReactNode,
    body?: ReactNode,
    className?: string,
    onClose?: () => void,
  ) => void
  const openModal2: (
    title: ReactNode,
    body?: ReactNode,
    className?: string,
    onClose?: () => void,
  ) => void
  const openConfirm: (data: OpenConfirm) => void
  const Row: typeof Component
  const toast: (
    value: ReactNode,
    theme?: string,
    expiry?: number,
    action?: { buttonText: string; onClick: () => void },
  ) => void
  const Flex: typeof Component
  const isMobile: boolean
  const FormGroup: typeof Component
  const Select: typeof _Select
  const Column: typeof Component
  const Loader: typeof Component
  const Input: typeof Component
  const Button: typeof Component
  const E2E: boolean
  const closeModal: () => void
  const closeModal2: () => void
  const toast: (message: string) => void
  const Tooltip: FC<TooltipProps>
  const API: {
    trackEvent: (data: {
      category: string
      event: string
      label?: string
      extra?: Record<string, any>
    }) => void
    trackTraits: (traits: Record<string, any>) => void
    [key: string]: any
  }
  const Utils: typeof Utils
  const AsyncStorage: {
    setItem: (key: string, value: string) => void
    getItem: (key: string) => string | null
    removeItem: (key: string) => void
    [key: string]: any
  }
  const PanelSearch: typeof Component
  const CodeHelp: typeof Component
  // Chargebee SDK (loaded via useScript)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Chargebee: any

  interface Window {
    E2E: boolean
  }
}

// Lets a style object set CSS custom properties, the one inline style the lint
// rule allows (runtime values feeding a SCSS class).
declare module 'react' {
  interface CSSProperties {
    [key: `--${string}`]: string | number | undefined
  }
}
