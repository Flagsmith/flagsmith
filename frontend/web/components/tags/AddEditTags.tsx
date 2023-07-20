import React, { FC, useMemo, useState } from 'react'
import { filter as loFilter } from 'lodash'
import { useHasPermission } from 'common/providers/Permission'
import Utils from 'common/utils/utils'
import InlineModal from 'components/InlineModal'
import Constants from 'common/constants'
import TagValues from './TagValues'
import { useDeleteTagMutation, useGetTagsQuery } from 'common/services/useTag'
import { Tag as TTag } from 'common/types/responses'
import Tag from './Tag'
import CreateEditTag from './CreateEditTag'
import Input from 'components/base/forms/Input'
import Button from 'components/base/forms/Button'
import ModalHR from 'components/modals/ModalHR'
import Icon from 'components/Icon'

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
          hideNames={false}
          projectId={projectId}
          onAdd={readOnly ? undefined : toggle}
          value={value}
        />
      </Row>
      {tab === 'SELECT' && !noTags && (
        <InlineModal
          title='Tags'
          isOpen={isOpen}
          onBack={() => setTab('SELECT')}
          showBack={tab !== 'SELECT'}
          onClose={toggle}
          className='inline-modal--tags pb-0'
          bottom={
            !readOnly && (
              <div className='text-right'>
                {Utils.renderWithPermission(
                  projectAdminPermission,
                  Constants.projectPermissions('Admin'),
                  <div className='inline-modal__buttons'>
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
                    ,
                  </div>,
                )}
              </div>
            )
          }
        >
          <div>
            <Input
              value={filter}
              onChange={(e: InputEvent) =>
                setFilter(Utils.safeParseEventValue(e))
              }
              className='full-width'
              placeholder='Search tags...'
              search
            />
            {tagsLoading && !projectTags && (
              <div className='text-center'>
                <Loader />
              </div>
            )}
            <div className='tag-list'>
              {filteredTags &&
                filteredTags.map((tag) => (
                  <div key={tag.id}>
                    <Row className='mt-4'>
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
                            className='clickable'
                          >
                            <Icon name='setting' fill='#9DA4AE' />
                          </div>
                          <div
                            onClick={() => confirmDeleteTag(tag)}
                            className='ml-2 clickable'
                          >
                            <Icon name='trash-2' fill='#9DA4AE' />
                          </div>
                        </>
                      )}
                    </Row>
                  </div>
                ))}
              {projectTags && projectTags.length && !filteredTags.length ? (
                <div className='text-center text-dark mt-4'>
                  No results for "<strong>{filter}</strong>"
                </div>
              ) : null}
              {noTags && (
                <div className='text-center text-dark mt-4'>You have no tags yet</div>
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
