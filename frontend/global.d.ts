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
type CrispCommand = [command: string, ...args: any[]]
type Crisp = {
  // The push method accepts a CrispCommand array.
  push: (command: CrispCommand) => void
}

export declare const openModal: (name?: string) => Promise<void>
declare global {
  const $crisp: Crisp
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
  const E2E: boolean
  const dtrum: undefined | { identifyUser: (id: string) => void }
  const closeModal: () => void
  const closeModal2: () => void
  const toast: (message: string) => void
  const Tooltip: FC<TooltipProps>
  interface Window {
    $crisp: Crisp
  }
}
