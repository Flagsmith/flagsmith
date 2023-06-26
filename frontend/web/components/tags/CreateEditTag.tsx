import React, { FC, KeyboardEvent, useEffect, useState } from 'react'
import { Tag as TTag } from 'common/types/responses'
import Constants from 'common/constants'
import Permission from 'common/providers/Permission'
import Utils from 'common/utils/utils'
import {
  useCreateTagMutation,
  useUpdateTagMutation,
} from 'common/services/useTag'

import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import Tag from './Tag'

type CreateEditTagType = {
  projectId: string
  onComplete?: (tag: TTag) => void
  tag?: TTag
}

const CreateEditTag: FC<CreateEditTagType> = ({
  onComplete: _onComplete,
  projectId,
  tag: _tag,
}) => {
  const [tag, setTag] = useState<Partial<TTag> | undefined>(_tag)
  const isEdit = !!tag?.id
  const [
    createTag,
    { data: createData, isLoading: creating, isSuccess: createSuccess },
  ] = useCreateTagMutation()
  const [
    editTag,
    { data: editData, isLoading: saving, isSuccess: editSuccess },
  ] = useUpdateTagMutation()
  const tagsSaving = creating || saving

  useEffect(() => {
    if (createSuccess && createData) {
      onComplete(createData)
    }
    //eslint-disable-next-line
  }, [createSuccess])
  useEffect(() => {
    if (createSuccess && editData) {
      onComplete(editData)
    }
    //eslint-disable-next-line
  }, [editSuccess])

  useEffect(() => {
    setTimeout(() => {
      document.getElementById('tag-label')?.focus()
    }, 500)
  }, [])

  const update = (index: keyof TTag, e: InputEvent | string) => {
    setTag({
      ...(tag || {}),
      [index]: Utils.safeParseEventValue(e),
    })
  }

  const onComplete = (tag: TTag) => {
    setTag(tag)
    _onComplete?.(tag)
  }

  const save = () => {
    const disabled = tagsSaving || !tag?.color || !tag?.label
    if (disabled) return
    if (isEdit) {
      editTag({ projectId, tag: tag as TTag })
    } else {
      createTag({ projectId, tag: tag as TTag })
    }
  }

  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
      save()
    }
  }

  return (
    <div>
      <InputGroup
        value={tag?.label}
        id='tag-label'
        inputProps={{
          className: 'full-width mb-2',
          name: 'create-tag-name',
          onKeyDown,
        }}
        title='Name'
        onChange={(e: InputEvent) => update('label', e)}
      />
      <InputGroup
        title='Select a color'
        component={
          <Row className='mb-2'>
            {Constants.tagColors.map((color) => (
              <div key={color} className='tag--select mr-2 mb-2'>
                <Tag
                  onClick={(e: TTag) => update('color', e.color)}
                  selected={tag?.color === color}
                  tag={{ color }}
                />
              </div>
            ))}
          </Row>
        }
      />
      <div className='text-center'>
        <Permission level='project' permission='ADMIN' id={projectId}>
          {({ permission }) =>
            Utils.renderWithPermission(
              permission,
              Constants.projectPermissions('Admin'),
              <div className='mx-2'>
                <Button
                  className='full-width'
                  onClick={save}
                  type='button'
                  disabled={
                    tagsSaving || !tag?.color || !tag?.label || !permission
                  }
                >
                  Save Tag
                </Button>
                ,
              </div>,
            )
          }
        </Permission>
      </div>
    </div>
  )
}

export default CreateEditTag
