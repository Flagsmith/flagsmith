import React, { FC, useEffect, useMemo, useState } from 'react'
import { filter as loFilter } from 'lodash'
import './AddEditTags.scss'
import { useHasPermission } from 'common/providers/Permission'
import Utils from 'common/utils/utils'
import { contentColours } from 'common/theme/tokens'
import InlineModal from 'components/InlineModal'
import TagRow from 'components/tags/TagRow'
import DropdownMenu from 'components/base/DropdownMenu'
import Constants from 'common/constants'
import TagValues from 'components/tags/TagValues'
import {
  useCreateTagMutation,
  useDeleteTagMutation,
  useGetTagsQuery,
} from 'common/services/useTag'
import { Tag as TTag } from 'common/types/responses'
import Tag from 'components/tags/Tag'
import CreateEditTag from 'components/tags/CreateEditTag'
import Input from 'components/base/forms/Input'
import Button from 'components/base/forms/Button'
import TagUsage from 'components/TagUsage'
import { ProjectPermission } from 'common/types/permissions.types'

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
  const { data, isLoading: tagsLoading } = useGetTagsQuery({
    projectId,
  })

  const unhealthyTagId = useMemo(() => {
    return data?.find((tag) => tag?.type === 'UNHEALTHY')?.id
  }, [data])

  // The unhealthy tag is applied by the system, never picked, so it stays out
  // of the list whatever the feature flag says. This used to keep it when the
  // flag was off and rely on Tag returning null to hide it again.
  const projectTags = useMemo(
    () => data?.filter((projectTag) => projectTag.type !== 'UNHEALTHY'),
    [data],
  )

  const [filter, setFilter] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [tag, setTag] = useState<TTag>()
  const [tab, setTab] = useState<'SELECT' | 'CREATE' | 'EDIT'>('SELECT')
  const [deleteTag] = useDeleteTagMutation()
  const [createTag] = useCreateTagMutation()

  const { permission: createEditTagPermission } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: ProjectPermission.MANAGE_TAGS,
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

  const palette = Object.values(contentColours)
  const color = palette[(projectTags?.length || 0) % palette.length]
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
          hideTags={unhealthyTagId ? [unhealthyTagId] : undefined}
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
              onChange={(e) => setFilter(Utils.safeParseEventValue(e))}
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
          containerClassName='px-0 py-2'
          bottom={
            !readOnly && (
              <div className='text-right'>
                {Utils.renderWithPermission(
                  createEditTagPermission,
                  Constants.projectPermissions(ProjectPermission.MANAGE_TAGS),
                  <div className='text-center'>
                    <Button
                      size='small'
                      className=''
                      disabled={!createEditTagPermission}
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
            <div className='tag-list d-flex flex-column'>
              {filteredTags &&
                filteredTags.map((tag) => (
                  <TagRow
                    checked={value?.includes(tag.id)}
                    disabled={Utils.tagDisabled(tag)}
                    key={tag.id}
                    onToggle={selectTag}
                    tag={tag}
                    trailing={
                      !readOnly &&
                      !!createEditTagPermission &&
                      !tag.is_system_tag && (
                        <DropdownMenu
                          items={[
                            {
                              icon: 'setting',
                              label: 'Edit',
                              onClick: () => editTag(tag),
                            },
                            {
                              className: 'text-danger',
                              icon: 'trash-2',
                              label: 'Delete',
                              onClick: () => confirmDeleteTag(tag),
                            },
                          ]}
                        />
                      )
                    }
                  />
                ))}
              {!!filter && !exactTag ? (
                <div
                  onClick={submit}
                  className='text-center flex-row text-default justify-content-center'
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
                <div className='text-center text-default mt-4'>
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
