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
type PylonConfig = {
  chat_settings: {
    app_id: string
    email: string
    name: string
    avatar_url?: string
    email_hash?: string
    account_id?: string
    account_external_id?: string
  }
}
type PylonFunction = {
  (command: 'show'): void
  (command: 'hide'): void
  (command: 'showChatBubble'): void
  (command: 'hideChatBubble'): void
  (command: 'onShow', callback: (() => void) | null): void
  (command: 'onHide', callback: (() => void) | null): void
  (
    command: 'onChangeUnreadMessagesCount',
    callback: ((count: number) => void) | null,
  ): void
  (command: 'setNewIssueCustomFields', fields: Record<string, any>): void
  (command: 'setTicketFormFields', fields: Record<string, any>): void
  (command: 'showNewMessage', message: string): void
  (command: 'showTicketForm', slug: string): void
  (command: 'showKnowledgeBaseArticle', articleId: string): void
  (...args: any[]): void
  q?: any[]
}
declare namespace UniversalAnalytics {
  interface PageviewFieldsObject {
    hitType: 'pageview' | 'event'
    location?: string
    page?: string
    title?: string
    [key: string]: any
  }
}
export declare const openModal: (name?: string) => Promise<void>
declare global {
  function ga(
    command: 'send',
    fields: UniversalAnalytics.PageviewFieldsObject,
  ): void
  const $crisp: Crisp
  const delighted: {
    survey: (opts: {
      createdAt: string
      email: string
      name: string
      properties: Record<string, any>
    }) => void
  }
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
  const closeModal: () => void
  const closeModal2: () => void
  const toast: (message: string) => void
  const Tooltip: FC<TooltipProps>
  interface Window {
    $crisp: Crisp
    Pylon: PylonFunction
    pylon: PylonConfig
    engagement: {
      init(apiKey: string, options?: InitOptions): void
      plugin(): unknown
      boot(options: BootOptions): Promise<void>
    }
  }
}
