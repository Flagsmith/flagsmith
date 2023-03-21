import React, { FC, useMemo, useState } from 'react'
import { filter as loFilter } from 'lodash'
import { useHasPermission } from 'common/providers/Permission'
import Utils from 'common/utils/utils'
import InlineModal from 'components/InlineModal'
import Constants from 'common/constants'
import TagValues from './TagValues'
import { useDeleteTagMutation, useGetTagsQuery } from 'common/services/useTag'
import { Tag as TTag } from 'common/types/responses'
import Button, { ButtonLink } from 'components/base/forms/Button'
import Tag from './Tag'
import CreateEditTag from './CreateEditTag'
import Input from 'components/base/forms/Input'

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
  const { permission: projectAdminPermission } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'ADMIN',
  })

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
    openConfirm(
      'Please confirm',
      'Are you sure you wish to delete this tag?',
      () => {
        onChange(loFilter(value || [], (id) => id !== tag.id))
        deleteTag({
          id: tag.id,
          projectId,
        })
        setIsOpen(true)
      },
    )
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

  const noTags = projectTags && !projectTags.length
  return (
    <div>
      <Row className='inline-tags mt-2'>
        <TagValues
          projectId={projectId}
          onAdd={readOnly ? undefined : toggle}
          value={value}
        />
      </Row>
      <InlineModal
        title='Tags'
        isOpen={isOpen}
        onBack={() => setTab('SELECT')}
        showBack={tab !== 'SELECT'}
        onClose={toggle}
        className='inline-modal--tags'
      >
        {tab === 'SELECT' && !noTags && (
          <div>
            <Input
              value={filter}
              onChange={(e: InputEvent) =>
                setFilter(Utils.safeParseEventValue(e))
              }
              className='full-width mb-2'
              placeholder='Search tags...'
            />
            {tagsLoading && !projectTags && (
              <div className='text-center'>
                <Loader />
              </div>
            )}
            <div className='tag-list'>
              {filteredTags &&
                filteredTags.map((tag, index) => (
                  <div key={tag.id}>
                    <Row className='py-2'>
                      <Flex>
                        <Tag
                          className='px-2 py-2'
                          onClick={selectTag}
                          selected={value?.includes(tag.id)}
                          tag={tag}
                        />
                      </Flex>
                      {!readOnly && !!projectAdminPermission && (
                        <>
                          <div
                            onClick={() => editTag(tag)}
                            className='ml-2 px-2 clickable'
                          >
                            <span className='icon ion-md-settings' />
                          </div>
                          <div
                            onClick={() => confirmDeleteTag(tag)}
                            className='ml-2 px-2 clickable'
                          >
                            <img
                              width={16}
                              src='/static/images/icons/bin.svg'
                            />
                          </div>
                        </>
                      )}
                    </Row>
                  </div>
                ))}
              {!readOnly && (
                <div className='text-center mb-2 mt-3'>
                  {Utils.renderWithPermission(
                    projectAdminPermission,
                    Constants.projectPermissions('Admin'),
                    <ButtonLink
                      disabled={!projectAdminPermission}
                      onClick={() => {
                        setTab('CREATE')
                        setFilter('')
                      }}
                      type='button'
                    >
                      Create a New Tag <span className='ml-3 icon ion-md-add' />
                    </ButtonLink>,
                  )}
                </div>
              )}
              {projectTags && projectTags.length && !filteredTags.length ? (
                <div className='text-center'>
                  No results for "<strong>{filter}</strong>"
                </div>
              ) : null}
              {noTags && (
                <div className='text-center'>You have no tags yet</div>
              )}
            </div>
          </div>
        )}

        {(tab === 'CREATE' || noTags) && (
          <CreateEditTag
            projectId={projectId}
            onComplete={(tag: TTag) => {
              selectTag(tag)
              setTab('SELECT')
            }}
          />
        )}
        {tab === 'EDIT' && (
          <CreateEditTag
            projectId={projectId}
            tag={tag}
            onComplete={(tag: TTag) => {
              selectTag(tag)
              setTab('SELECT')
            }}
          />
        )}
      </InlineModal>
    </div>
  )
}

export default AddEditTags
