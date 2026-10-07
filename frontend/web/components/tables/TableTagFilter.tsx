import React, { FC, useState } from 'react'
import TableFilter from './TableFilter'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { useGetTagsQuery } from 'common/services/useTag'
import ColorSwatch from 'components/ColorSwatch'
import { getTagColor } from 'components/tags/Tag'
import TableFilterItem from './TableFilterItem'
import Constants from 'common/constants'
import { TagStrategy } from 'common/types/responses'
import TagContent from 'components/tags/TagContent'

type TableFilterType = {
  projectId: number
  value: (number | string)[] | undefined
  isLoading: boolean
  onChange: (value: (number | string)[], isAutomatedChange?: boolean) => void
  showArchived: boolean
  onToggleArchived: (value: boolean) => void
  className?: string
  tagStrategy: TagStrategy
  onChangeStrategy: (value: TagStrategy) => void
  excludeTag?: (tag: { type: string; is_permanent: boolean }) => boolean
}

const TableTagFilter: FC<TableFilterType> = ({
  className,
  excludeTag,
  isLoading,
  onChange,
  onChangeStrategy,
  onToggleArchived,
  projectId,
  showArchived,
  tagStrategy,
  value,
}) => {
  const [filter, setFilter] = useState('')
  const { data } = useGetTagsQuery(
    { projectId: `${projectId}` },
    { skip: !projectId },
  )

  // Not memoised: tagVisible reads a feature flag that arrives after the first
  // render, and a dependency array cannot see that. The list is small.
  const flagGatedTags = data?.filter(
    (tag) => Utils.tagVisible(tag) && (!excludeTag || !excludeTag(tag)),
  )

  const filteredTags = filter
    ? flagGatedTags?.filter((v) => v.label.toLowerCase().includes(filter))
    : flagGatedTags
  const length = (value?.length || 0) + (showArchived ? 1 : 0)
  return (
    <div className={isLoading ? 'disabled' : ''}>
      <TableFilter
        data-test='table-filter-tags'
        className={className}
        dropdownTitle={
          <>
            <div className='full-width'>
              <Select
                size='select-xxsm'
                styles={{
                  control: (base) => ({
                    ...base,
                    height: 18,
                  }),
                }}
                onChange={(v) => {
                  if (v) onChangeStrategy(v.value)
                }}
                value={{
                  label:
                    tagStrategy === 'INTERSECTION' ? 'Has all' : 'Has some',
                  value: tagStrategy,
                }}
                options={[
                  {
                    label: 'Has all',
                    value: 'INTERSECTION',
                  },
                  {
                    label: 'Has some',
                    value: 'UNION',
                  },
                ]}
              />
            </div>
          </>
        }
        title={
          <Row>
            Tags{' '}
            {!!length && <span className='mx-1 unread d-inline'>{length}</span>}
          </Row>
        }
      >
        <div className='inline-modal__list d-flex flex-column mx-0 py-0'>
          <div className='px-2 my-2'>
            <Input
              autoFocus
              onChange={(e) => {
                setFilter(Utils.safeParseEventValue(e))
              }}
              className='full-width'
              value={filter}
              type='text'
              size='xSmall'
              placeholder='Search'
              search
            />
          </div>
          {filteredTags?.length === 0 && (
            <div className='text-center'>No tags</div>
          )}
          <div className='table-filter-list'>
            <TableFilterItem
              onClick={() => {
                if (!isLoading) {
                  onToggleArchived(!showArchived)
                }
              }}
              isActive={showArchived}
              title={
                <Row className='overflow-hidden'>
                  <ColorSwatch
                    color={getTagColor(Constants.archivedTag)}
                    shape='circle'
                    size='lg'
                  />
                  <div className='ml-2 text-overflow'>archived</div>
                </Row>
              }
            />
            <TableFilterItem
              onClick={() => {
                if (value?.includes('')) {
                  onChange((value || []).filter((v) => v !== ''))
                } else {
                  onChange((value || []).concat(['']))
                }
              }}
              isActive={value?.includes('')}
              title={
                <Row className='overflow-hidden'>
                  <ColorSwatch
                    color={getTagColor(Constants.untaggedTag)}
                    shape='circle'
                    size='lg'
                  />
                  <div className='ml-2 text-overflow'>untagged</div>
                </Row>
              }
            />
            {filteredTags?.map((tag) => (
              <TableFilterItem
                onClick={() => {
                  const disabled = Utils.tagDisabled(tag)
                  if (disabled) {
                    return
                  }
                  if (isLoading) {
                    return
                  }
                  if (value?.includes(tag.id)) {
                    onChange((value || []).filter((v) => v !== tag.id))
                  } else {
                    onChange((value || []).concat([tag.id]))
                  }
                }}
                isActive={value?.includes(tag.id)}
                title={
                  <Row>
                    <ColorSwatch
                      color={getTagColor(tag)}
                      key={tag.id}
                      shape='circle'
                      size='lg'
                    />
                    <div
                      style={{ width: 150 }}
                      className='ml-2 text-nowrap text-overflow'
                    >
                      <TagContent tag={tag} />
                    </div>
                  </Row>
                }
                key={tag.id}
              />
            ))}
          </div>
        </div>
      </TableFilter>
    </div>
  )
}

export default TableTagFilter
