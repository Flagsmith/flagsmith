import { Component, FC, ReactNode } from 'react'
import _Select from './web/components/Select'

export declare const openModal: (name?: string) => Promise<void>
declare global {
  const openModal: (
    title: ReactNode,
    body?: ReactNode,
    footer?: ReactNode,
    other?: { className: string; onClose?: () => void },
  ) => void
  const openConfirm: (
    header: ReactNode,
    body: ReactNode,
    onYes: () => void,
    onNo?: () => void,
    yesText?: string,
    noText?: string,
  ) => void
  const Row: typeof Component
  const toast: (value: string) => void
  const Flex: typeof Component
  const isMobile: boolean
  const FormGroup: typeof Component
  const Select: typeof _Select
  const Column: typeof Component
  const RemoveIcon: typeof Component
  const Loader: typeof Component
  const E2E: boolean
  const closeModal: () => void
  const toast: (message: string) => void
  const Tooltip: FC<{
    title: ReactNode
    children: ReactNode
    place?: string
    html?: boolean
  }>
}
