import React, { FC, useMemo, useState } from 'react'
import TableFilter from './TableFilter'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { useGetTagsQuery } from 'common/services/useTag'
import Tag from 'components/tags/Tag'
import TableFilterItem from './TableFilterItem'
import Constants from 'common/constants'

type TableFilterType = {
  projectId: string
  value: number[] | undefined
  onChange: (value: number[]) => void
  showArchived: boolean
  onToggleArchived: () => void
  className?: string
}

const TableTagFilter: FC<TableFilterType> = ({
  className,
  onChange,
  onToggleArchived,
  projectId,
  showArchived,
  value,
}) => {
  const [filter, setFilter] = useState('')
  const { data } = useGetTagsQuery({ projectId })
  const filteredTags = useMemo(() => {
    return filter
      ? data?.filter((v) => v.label.toLowerCase().includes(filter))
      : data
  }, [data, filter])
  const length = (value?.length || 0) + (showArchived ? 1 : 0)
  return (
    <>
      <TableFilter
        className={className}
        dropdownTitle={
          <Input
            autoFocus
            onChange={(e: InputEvent) => {
              setFilter(Utils.safeParseEventValue(e))
            }}
            className='full-width'
            value={filter}
            type='text'
            size='xSmall'
            placeholder='Search'
            search
          />
        }
        title={
          <Row>
            Tags{' '}
            {!!length && <span className='mx-1 unread d-inline'>{length}</span>}
          </Row>
        }
      >
        <div className='inline-modal__list d-flex flex-column mx-0 py-0'>
          {filteredTags?.length === 0 && (
            <div className='text-center'>No tags</div>
          )}
          <TableFilterItem
            onClick={onToggleArchived}
            isActive={showArchived}
            title={
              <Row>
                <Tag
                  isDot
                  selected={showArchived}
                  className='px-2 py-2 mr-1'
                  tag={Constants.archivedTag}
                />
                <div className='ml-2'>archived</div>
              </Row>
            }
          />
          {filteredTags?.map((tag) => (
            <TableFilterItem
              onClick={() => {
                if (value?.includes(tag.id)) {
                  onChange((value || []).filter((v) => v !== tag.id))
                } else {
                  onChange((value || []).concat([tag.id]))
                }
              }}
              isActive={value?.includes(tag.id)}
              title={
                <Row>
                  <Tag
                    key={tag.id}
                    isDot
                    selected={value?.includes(tag.id)}
                    className='px-2 py-2 mr-1'
                    tag={tag}
                  />
                  <div className='ml-2'>{tag.label}</div>
                </Row>
              }
              key={tag.id}
            />
          ))}
        </div>
      </TableFilter>
    </>
  )
}

export default TableTagFilter
