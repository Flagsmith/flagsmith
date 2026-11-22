import React, { FC } from 'react'
import Row from 'components/base/grid/Row'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import { Tag as TTag } from 'common/types/responses'
import Tag from 'components/tags/Tag'
import TagContent from 'components/tags/TagContent'
import TableFilterItem from './TableFilterItem'
import { matchesTagFilter } from './tableTagFilterUtils'

type TableTagFilterOptionsProps = {
  filter: string
  isLoading: boolean
  onChange: (value: (number | string)[], isAutomatedChange?: boolean) => void
  onToggleArchived: (value: boolean) => void
  showArchived: boolean
  tags: TTag[] | undefined
  value: (number | string)[] | undefined
}

const TableTagFilterOptions: FC<TableTagFilterOptionsProps> = ({
  filter,
  isLoading,
  onChange,
  onToggleArchived,
  showArchived,
  tags,
  value,
}) => {
  const filteredTags = tags?.filter((tag) =>
    matchesTagFilter(tag.label, filter),
  )
  const showArchivedOption = matchesTagFilter('archived', filter)
  const showUntaggedOption = matchesTagFilter('untagged', filter)

  return (
    <>
      {filteredTags?.length === 0 &&
        !showArchivedOption &&
        !showUntaggedOption && <div className='text-center'>No tags</div>}
      <div className='table-filter-list'>
        {showArchivedOption && (
          <TableFilterItem
            onClick={() => {
              if (!isLoading) {
                onToggleArchived(!showArchived)
              }
            }}
            isActive={showArchived}
            title={
              <Row className='overflow-hidden'>
                <Tag
                  isDot
                  selected={showArchived}
                  className='px-2 py-2 mr-1'
                  tag={Constants.archivedTag}
                />
                <div className='ml-2 text-overflow'>archived</div>
              </Row>
            }
          />
        )}
        {showUntaggedOption && (
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
                <Tag
                  isDot
                  selected={value?.includes('')}
                  className='px-2 py-2 mr-1'
                  tag={Constants.untaggedTag}
                />
                <div className='ml-2 text-overflow'>untagged</div>
              </Row>
            }
          />
        )}
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
                <Tag
                  key={tag.id}
                  isDot
                  selected={value?.includes(tag.id)}
                  className='px-2 py-2 mr-1'
                  tag={tag}
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
    </>
  )
}

export default TableTagFilterOptions
