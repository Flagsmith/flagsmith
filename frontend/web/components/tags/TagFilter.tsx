import React, { FC, ReactNode } from 'react'
import { filter } from 'lodash'
import { Tag as TTag } from 'common/types/responses'
import { useGetTagsQuery } from 'common/services/useTag'
import Tag from './Tag'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'

type TagFilterType = {
  value?: (number | string)[]
  onClearAll?: () => void
  showClearAll?: boolean
  showUntagged?: boolean
  projectId: string
  onChange: (value: (number | string)[]) => void
  children?: ReactNode
}

const TagFilter: FC<TagFilterType> = ({
  children,
  onChange,
  onClearAll,
  projectId,
  showClearAll,
  showUntagged,
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
    color: Utils.getFlagsmithHasFeature('dark_mode') ? '#FFFFF' : '#1A2634',
    id: '',
    label: 'Untagged',
  }
  return (
    <Row className='tag-filter mx-2 mt-4'>
      <div className='ml-1'>
        <Row>
          <Flex>
            <Row className='tag-filter-list'>
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
