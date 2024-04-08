import React, { FC, useEffect, useMemo, useState } from 'react'
import { filter as loFilter } from 'lodash'
import { useHasPermission } from 'common/providers/Permission'
import Utils from 'common/utils/utils'
import InlineModal from 'components/InlineModal'
import Constants from 'common/constants'
import TagValues from './TagValues'
import {
  useCreateTagMutation,
  useDeleteTagMutation,
  useGetTagsQuery,
} from 'common/services/useTag'
import { Tag as TTag } from 'common/types/responses'
import Tag from './Tag'
import CreateEditTag from './CreateEditTag'
import Input from 'components/base/forms/Input'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import TagUsage from 'components/TagUsage'

type AddEditTagsType = {
  value?: number[]
  readOnly?: boolean
  onChange: (value: number[]) => void
  projectId: string
}

const AddEditTags: FC<AddEditTagsType> = ({
  onChange,
  projectId,
  readOnly,
  value,
}) => {
  const { data: projectTags, isLoading: tagsLoading } = useGetTagsQuery({
    projectId,
  })
  const [filter, setFilter] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [tag, setTag] = useState<TTag>()
  const [tab, setTab] = useState<'SELECT' | 'CREATE' | 'EDIT'>('SELECT')
  const [deleteTag] = useDeleteTagMutation()
  const [createTag] = useCreateTagMutation()
  const { permission: projectAdminPermission } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'ADMIN',
  })

  useEffect(() => {
    if (!isOpen) {
      setTab('SELECT')
    }
  }, [isOpen])
  const selectTag = (tag: TTag) => {
    const _value = value || []
    const isSelected = _value?.includes(tag.id)
    if (isSelected) {
      onChange(loFilter(_value, (id) => id !== tag.id))
    } else {
      onChange(_value.concat([tag.id]))
    }
  }

  const toggle = () => setIsOpen(!isOpen)

  const editTag = (tag: TTag) => {
    setTag(tag)
    setTab('EDIT')
  }

  const confirmDeleteTag = (tag: TTag) => {
    openConfirm({
      body: (
        <div>
          Are you sure you wish to delete the tag{' '}
          <div className='d-inline-block'>
            <Tag tag={tag} />
          </div>
          ? This action cannot be undone.
          <TagUsage projectId={projectId} tag={tag.id} />
        </div>
      ),
      destructive: true,
      onYes: () => {
        onChange(loFilter(value || [], (id) => id !== tag.id))
        deleteTag({
          id: tag.id,
          projectId,
        })
        setIsOpen(true)
      },
      title: 'Delete tag',
      yesText: 'Confirm',
    })
  }

  const filteredTags = useMemo(() => {
    const _filter = filter.toLowerCase()
    if (_filter) {
      return loFilter(projectTags, (tag) =>
        tag.label.toLowerCase().includes(filter),
      )
    }
    return projectTags || []
  }, [filter, projectTags])

  const exactTag = useMemo(() => {
    const _filter = filter.toLowerCase()
    if (_filter) {
      return projectTags?.find((tag) => tag.label === filter)
    }
    return null
  }, [filter, projectTags])
  const noTags = projectTags && !projectTags.length

  const color =
    Constants.tagColors[projectTags?.length || 0] || Constants.tagColors[0]
  const submit = () => {
    createTag({
      projectId,
      tag: { color, description: '', label: filter, project: projectId },
    }).then((res) => {
      if (!res?.error && res.data) {
        selectTag(res.data)
        setFilter('')
      }
    })
  }
  return (
    <div>
      <Row className='inline-tags mt-2'>
        <TagValues
          hideNames={false}
          projectId={projectId}
          onAdd={readOnly ? undefined : toggle}
          value={value}
        />
      </Row>
      {tab === 'SELECT' && !noTags && (
        <InlineModal
          hideClose
          title={
            <Input
              autoFocus
              value={filter}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  submit()
                }
              }}
              onChange={(e: InputEvent) =>
                setFilter(Utils.safeParseEventValue(e))
              }
              size='xSmall'
              className='full-width'
              placeholder='Search tags...'
              search
            />
          }
          isOpen={isOpen}
          onBack={() => setTab('SELECT')}
          showBack={tab !== 'SELECT'}
          onClose={toggle}
          className='inline-modal--sm pb-0'
          bottom={
            !readOnly && (
              <div className='text-right'>
                {Utils.renderWithPermission(
                  projectAdminPermission,
                  Constants.projectPermissions('Admin'),
                  <div className='text-center'>
                    <Button
                      className=''
                      disabled={!projectAdminPermission}
                      onClick={() => {
                        setTab('CREATE')
                        setFilter('')
                      }}
                      type='button'
                    >
                      Add New Tag
                    </Button>
                  </div>,
                )}
              </div>
            )
          }
        >
          <div>
            {tagsLoading && !projectTags && (
              <div className='text-center'>
                <Loader />
              </div>
            )}
            <div className='tag-list d-flex flex-column gap-4'>
              {filteredTags &&
                filteredTags.map((tag) => (
                  <div key={tag.id}>
                    <Row>
                      <Flex>
                        <Tag
                          className='px-2 py-2'
                          onClick={selectTag}
                          selected={value?.includes(tag.id)}
                          tag={tag}
                        />
                      </Flex>
                      {!readOnly &&
                        !!projectAdminPermission &&
                        !tag.is_system_tag && (
                          <>
                            <div
                              onClick={() => editTag(tag)}
                              className='clickable'
                            >
                              <Icon name='setting' fill='#9DA4AE' />
                            </div>
                            <div
                              onClick={() => confirmDeleteTag(tag)}
                              className='ml-3 clickable'
                            >
                              <Icon name='trash-2' fill='#9DA4AE' />
                            </div>
                          </>
                        )}
                    </Row>
                  </div>
                ))}
              {!!filter && !exactTag ? (
                <div
                  onClick={submit}
                  className='text-center flex-row text-dark justify-content-center'
                >
                  <div className='me-2'>Create</div>
                  <Tag
                    className='truncated-tag'
                    tag={{
                      color,
                      label: filter,
                    }}
                  />
                </div>
              ) : null}
              {noTags && (
                <div className='text-center text-dark mt-4'>
                  You have no tags yet
                </div>
              )}
            </div>
          </div>
        </InlineModal>
      )}
      {(tab === 'CREATE' || noTags) && (
        <CreateEditTag
          onClose={toggle}
          isOpen={isOpen}
          projectId={projectId}
          title='Create tag'
          onBack={() => setTab('SELECT')}
          onComplete={(tag: TTag) => {
            selectTag(tag)
            setTab('SELECT')
          }}
        />
      )}
      {tab === 'EDIT' && (
        <CreateEditTag
          title='Edit tag'
          onClose={toggle}
          onBack={() => setTab('SELECT')}
          isOpen={isOpen}
          projectId={projectId}
          tag={tag}
          onComplete={(tag: TTag) => {
            selectTag(tag)
            setTab('SELECT')
          }}
        />
      )}
    </div>
  )
}

export default AddEditTags
