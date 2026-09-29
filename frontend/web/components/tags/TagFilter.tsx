import React, { FC, ReactNode } from 'react'
import { filter } from 'lodash'
import { Tag as TTag, TagStrategy } from 'common/types/responses'

type TagId = number | string
const UNTAGGED_ID = ''
import { useGetTagsQuery } from 'common/services/useTag'
import Tag from './Tag'
import Button from 'components/base/forms/Button'

type TagFilterType = {
  value?: TagId[]
  onClearAll?: () => void
  showClearAll?: boolean
  showUntagged?: boolean
  tagStrategy: TagStrategy
  onChangeStrategy?: (value: TagStrategy) => void
  projectId: string
  onChange: (value: TagId[]) => void
  children?: ReactNode
}

const TagFilter: FC<TagFilterType> = ({
  children,
  onChange,
  onChangeStrategy,
  onClearAll,
  projectId,
  showClearAll,
  showUntagged,
  tagStrategy,
  value: _value,
}) => {
  const { data: projectTags } = useGetTagsQuery({
    projectId,
  })

  // Both only ever read the id, and the untagged pseudo-tag has a string one.
  const isSelected = (id: TagId) => _value?.includes(id)
  const onSelect = (id: TagId) => {
    const value = _value || []
    if (value.includes(id)) {
      onChange(filter(value, (v) => v !== id))
    } else {
      onChange(value.concat([id]))
    }
  }

  // Not a tag: it stands for the absence of one, so it has no row behind it.
  const unTagged: Partial<TTag> = { color: '#656D7B', label: 'Untagged' }
  return (
    <Row className='tag-filter mt-2'>
      <div className='ml-1'>
        <Row>
          <Flex>
            <Row className='gap-2'>
              {!!onChangeStrategy && (
                <div style={{ width: 140 }}>
                  <Select
                    size='select-xxsm'
                    styles={{
                      control: (base) => ({
                        ...base,
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
              )}
              {showUntagged && (
                <Tag
                  key={UNTAGGED_ID}
                  selected={isSelected(UNTAGGED_ID)}
                  onClick={() => onSelect(UNTAGGED_ID)}
                  className='px-2 py-2'
                  tag={unTagged}
                />
              )}
              {children}

              {projectTags?.map((tag) => (
                <Tag
                  key={tag.id}
                  selected={isSelected(tag.id)}
                  onClick={() => onSelect(tag.id)}
                  className='px-2 py-2 mr-1'
                  tag={tag}
                />
              ))}
            </Row>
          </Flex>

          {showClearAll && (
            <Button
              onClick={() => {
                if ((_value?.length || 0) >= (projectTags?.length || 0)) {
                  onChange([])
                } else {
                  onChange(
                    (showUntagged ? [''] : []).concat(
                      // @ts-ignore mixed array type
                      (projectTags || [])?.map((v) => v.id),
                    ),
                  )
                }
                onClearAll && onClearAll()
              }}
              className='mr-2'
              theme='outline'
              size='xSmall'
            >
              Clear Filters
            </Button>
          )}
        </Row>
      </div>
    </Row>
  )
}

export default TagFilter
