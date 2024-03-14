import React, { FC, useEffect, useMemo, useRef, useState } from 'react'
import TableFilter from './TableFilter'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { useGetTagsQuery } from 'common/services/useTag'
import Tag from 'components/tags/Tag'
import TableFilterItem from './TableFilterItem'
import Constants from 'common/constants'
import { TagStrategy } from 'common/types/responses'
import { AsyncStorage } from 'polyfill-react-native'

type TableFilterType = {
  projectId: string
  value: (number | string)[] | undefined
  isLoading: boolean
  onChange: (value: (number | string)[], isAutomatedChange?: boolean) => void
  showArchived: boolean
  onToggleArchived: (value: boolean) => void
  className?: string
  tagStrategy: TagStrategy
  onChangeStrategy: (value: TagStrategy, isAutomatedChange?: boolean) => void
  useLocalStorage?: boolean
}

const TableTagFilter: FC<TableFilterType> = ({
  className,
  isLoading,
  onChange,
  onChangeStrategy,
  onToggleArchived,
  projectId,
  showArchived,
  tagStrategy,
  useLocalStorage,
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
  const checkedLocalStorage = useRef(false)
  useEffect(() => {
    const checkLocalStorage = async function () {
      if (useLocalStorage && !checkedLocalStorage.current && data) {
        checkedLocalStorage.current = true
        const [tags, showArchived, tagStrategy] = await Promise.all([
          AsyncStorage.getItem(`${projectId}-tags`),
          AsyncStorage.getItem(`${projectId}-showArchived`),
          AsyncStorage.getItem(`${projectId}-tagStrategy`),
        ])
        if (tags) {
          try {
            const storedTags = JSON.parse(tags)
            onChange(
              storedTags.filter(
                (v) => v === '' || !!data.find((tag) => tag.id === v),
              ),
              true,
            )
          } catch (e) {}
        }
        if (showArchived) {
          onToggleArchived(showArchived === 'true')
        }
        if (tagStrategy) {
          onChangeStrategy(tagStrategy, true)
        }
      }
    }
    checkLocalStorage()
  }, [useLocalStorage, data])
  return (
    <div className={isLoading ? 'disabled' : ''}>
      <TableFilter
        className={className}
        dropdownTitle={
          <>
            <div className='full-width'>
              <Select
                size='select-xxsm'
                styles={{
                  control: (base) => ({
                    ...base,
                    '&:hover': { borderColor: '$bt-brand-secondary' },
                    border: '1px solid $bt-brand-secondary',
                    height: 18,
                  }),
                }}
                onChange={(v) => {
                  onChangeStrategy(v!.value)
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
          <div className='px-2 mt-2'>
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
          </div>
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
          {filteredTags?.map((tag) => (
            <TableFilterItem
              onClick={() => {
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
                  <div className='ml-2'>{tag.label}</div>
                </Row>
              }
              key={tag.id}
            />
          ))}
        </div>
      </TableFilter>
    </div>
  )
}

export default TableTagFilter
