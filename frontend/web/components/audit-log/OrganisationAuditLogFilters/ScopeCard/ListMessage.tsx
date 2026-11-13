import { FC } from 'react'
import classNames from 'classnames'

export type ScopeList<T> = {
  items: T[]
  loading: boolean
  failed: boolean
}

type ListMessageProps = {
  list: ScopeList<unknown>
  noun: string
  emptyText: string
}

export const getListMessage = ({ emptyText, list, noun }: ListMessageProps) => {
  if (list.failed) return { isError: true, text: `Couldn't load ${noun}` }
  if (list.loading) return { isError: false, text: `Loading ${noun}…` }
  if (!list.items.length) return { isError: false, text: emptyText }
  return null
}

const ListMessage: FC<ListMessageProps> = (props) => {
  const message = getListMessage(props)
  if (!message) return null
  return (
    <span
      className={classNames('fs-caption p-2', {
        'text-danger': message.isError,
        'text-secondary': !message.isError,
      })}
    >
      {message.text}
    </span>
  )
}

export default ListMessage
