import React, { FC, useMemo, useState } from 'react'
import TableFilter from './TableFilter'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { useGetTagsQuery } from 'common/services/useTag'
import Tag from 'components/tags/Tag'
import TableFilterItem from './TableFilterItem'
import Constants from 'common/constants'
import { TagStrategy } from 'common/types/responses'
import TagContent from 'components/tags/TagContent'

// Not a tag: it stands for the absence of one, so it has no row behind it.
const UNTAGGED_ID = ''

// The two rows with no tag behind them, so the search can reach them too.
const ARCHIVED_LABEL = 'archived'
const UNTAGGED_LABEL = 'untagged'

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

  const isFeatureHealthEnabled = Utils.getFlagsmithHasFeature('feature_health')
  const flagGatedTags = useMemo(() => {
    let tags = data
    if (!isFeatureHealthEnabled)
      tags = tags?.filter((tag) => tag.type !== 'UNHEALTHY')
    if (excludeTag) tags = tags?.filter((tag) => !excludeTag(tag))
    return tags
  }, [data, isFeatureHealthEnabled, excludeTag])

  const search = filter.trim().toLowerCase()
  const filteredTags = useMemo(() => {
    if (!search) return flagGatedTags
    return flagGatedTags?.filter((v) => v.label.toLowerCase().includes(search))
  }, [flagGatedTags, search])

  const showArchivedRow = ARCHIVED_LABEL.includes(search)
  const showUntaggedRow = UNTAGGED_LABEL.includes(search)
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
          {filteredTags?.length === 0 &&
            !showArchivedRow &&
            !showUntaggedRow && <div className='text-center'>No tags</div>}
          <div className='table-filter-list'>
            {showArchivedRow && (
              <TableFilterItem
                onClick={() => {
                  if (!isLoading) {
                    onToggleArchived(!showArchived)
                  }
                }}
                isActive={showArchived}
                title={
                  <Row className='overflow-hidden'>
                    <Tag isDot tag={Constants.archivedTag} />
                    <div className='ml-2 text-overflow'>{ARCHIVED_LABEL}</div>
                  </Row>
                }
              />
            )}
            {showUntaggedRow && (
              <TableFilterItem
                onClick={() => {
                  if (value?.includes(UNTAGGED_ID)) {
                    onChange((value || []).filter((v) => v !== UNTAGGED_ID))
                  } else {
                    onChange((value || []).concat([UNTAGGED_ID]))
                  }
                }}
                isActive={value?.includes(UNTAGGED_ID)}
                title={
                  <Row className='overflow-hidden'>
                    <Tag isDot tag={Constants.untaggedTag} />
                    <div className='ml-2 text-overflow'>{UNTAGGED_LABEL}</div>
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
                    <Tag key={tag.id} isDot tag={tag} />
                    <div
                      style={{ width: 150 }}
                      className='ml-2 text-nowrap text-overflow'
                    >
                      <TagContent disabled={Utils.tagDisabled(tag)} tag={tag} />
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
