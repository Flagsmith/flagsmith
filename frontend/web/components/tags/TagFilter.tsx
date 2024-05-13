import React, { FC, ReactNode } from 'react'
import { filter } from 'lodash'
import { Tag as TTag, TagStrategy } from 'common/types/responses'
import { useGetTagsQuery } from 'common/services/useTag'
import Tag from './Tag'
import Button from 'components/base/forms/Button'

type TagFilterType = {
  value?: (number | string)[]
  onClearAll?: () => void
  showClearAll?: boolean
  showUntagged?: boolean
  tagStrategy: TagStrategy
  onChangeStrategy?: (value: TagStrategy) => void
  projectId: string
  onChange: (value: (number | string)[]) => void
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

  const isSelected = (tag: TTag) => _value?.includes(tag?.id)
  const onSelect = (tag: TTag) => {
    const value = _value || []
    if (value.includes(tag.id)) {
      onChange(filter(value, (v) => v !== tag.id))
    } else {
      onChange(value.concat([tag.id]))
    }
  }
  const unTagged = !!showUntagged && {
    color: '#656D7B',
    id: '',
    label: 'Untagged',
  }
  return (
    <Row className='tag-filter mt-2'>
      <div className='ml-1'>
        <Row>
          <Flex>
            <Row className='tag-filter-list'>
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
              {unTagged && (
                <Tag
                  key={unTagged.id}
                  selected={isSelected(unTagged as any)}
                  onClick={onSelect}
                  className='px-2 py-2'
                  tag={unTagged as any}
                />
              )}
              {children}

              {projectTags?.map((tag) => (
                <Tag
                  key={tag.id}
                  selected={isSelected(tag)}
                  onClick={onSelect}
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
