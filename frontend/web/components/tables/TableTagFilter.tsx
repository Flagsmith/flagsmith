import React, { FC, useMemo, useState } from 'react'
import TableFilter from './TableFilter'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { useGetTagsQuery } from 'common/services/useTag'
import { TagStrategy } from 'common/types/responses'
import TableTagFilterOptions from './TableTagFilterOptions'

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
          <TableTagFilterOptions
            filter={filter}
            isLoading={isLoading}
            onChange={onChange}
            onToggleArchived={onToggleArchived}
            showArchived={showArchived}
            tags={flagGatedTags}
            value={value}
          />
        </div>
      </TableFilter>
    </div>
  )
}

export default TableTagFilter
