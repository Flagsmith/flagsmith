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
import BareButton from 'components/base/forms/BareButton'
import Icon from 'components/icons/Icon'
import CreateEditTag from 'components/tags/CreateEditTag'
import Input from 'components/base/forms/Input'
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

  // Trimmed, so the duplicate check and the tag it creates agree.
  const newLabel = filter.trim()
  const search = newLabel.toLowerCase()

  const filteredTags = useMemo(() => {
    if (!search) return projectTags || []
    return loFilter(projectTags, (tag) =>
      tag.label.toLowerCase().includes(search),
    )
  }, [search, projectTags])

  // Case-insensitive, or the box offers to create a name that is already taken.
  const exactTag = useMemo(
    () => projectTags?.find((tag) => tag.label.toLowerCase() === search),
    [search, projectTags],
  )
  const noTags = projectTags && !projectTags.length
  // Nothing to create when the box is empty, or when the name is already taken.
  const canCreate = !!search && !exactTag

  const palette = Object.values(contentColours)
  const color = palette[(projectTags?.length || 0) % palette.length]
  const submit = () => {
    createTag({
      projectId,
      tag: { color, description: '', label: newLabel, project: projectId },
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
              onKeyDown={(e) => {
                if (e.key === 'Enter' && canCreate) {
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
          onClose={toggle}
          className='inline-modal--sm pb-0'
          containerClassName='px-0 py-2'
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
            </div>
            {/* The only way to make a tag, and outside the scrolling list so
                it stays in reach. Named, it creates one; unnamed, it opens
                the full form. */}
            {!readOnly &&
              Utils.renderWithPermission(
                createEditTagPermission,
                Constants.projectPermissions(ProjectPermission.MANAGE_TAGS),
                <BareButton
                  className='tag-create d-flex align-items-center gap-2 w-100 text-default'
                  disabled={!createEditTagPermission}
                  onClick={
                    canCreate
                      ? submit
                      : () => {
                          setTab('CREATE')
                          setFilter('')
                        }
                  }
                >
                  <Icon name='plus' width={16} />
                  <span className='text-truncate'>
                    {canCreate ? `Create "${newLabel}"` : 'New tag'}
                  </span>
                  {/* Enter does the same thing, so the row says so. */}
                  {canCreate && (
                    <kbd className='tag-create__enter ms-auto rounded-sm bg-surface-subtle text-secondary'>
                      &#9166;
                    </kbd>
                  )}
                </BareButton>,
              )}
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
