import React, {
  useState,
  useRef,
  useEffect,
  FormEvent,
  ChangeEvent,
  FC,
} from 'react'
import Highlight from 'components/Highlight'
import Constants from 'common/constants'
import Format from 'common/utils/format'
import ErrorMessage from 'components/ErrorMessage'
import ModalHR from './ModalHR'
import IdentityProvider from 'common/providers/IdentityProvider'
import _ from 'lodash'
import ProjectProvider from 'common/providers/ProjectProvider'
import Button from 'components/base/forms/Button'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import {
  useCreateIdentityTraitMutation,
  useUpdateIdentityTraitMutation,
} from 'common/services/useIdentityTrait'

type CreateTraitProps = {
  id?: string
  trait_key?: string
  trait_value?: string
  identityName: string
  onSave?: () => void
  identity: string
  isEdit: boolean
  projectId: string | number
  environmentId: string
}

const CreateTrait: FC<CreateTraitProps> = ({
  environmentId,
  id,
  identity,
  identityName,
  isEdit,
  onSave,
  projectId,
  trait_key: initialTraitKey = '',
  trait_value: initialTraitValue = '',
}) => {
  const [traitKey, setTraitKey] = useState<string>(initialTraitKey)
  const [traitValue, setTraitValue] = useState<any>(initialTraitValue)
  const use_edge_identities = Utils.getIsEdge()

  const [createTrait, { error: createError, isLoading: isCreating }] =
    useCreateIdentityTraitMutation()
  const [updateTrait, { error: updateError, isLoading: isUpdating }] =
    useUpdateIdentityTraitMutation()
  const error = createError || updateError
  const isLoading = isCreating || isUpdating
  const inputRef = useRef<any>(null)
  const focusTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!isEdit) {
      focusTimeoutRef.current = setTimeout(() => {
        if (inputRef.current && inputRef.current.focus) {
          inputRef.current.focus()
        }
        focusTimeoutRef.current = null
      }, 500)
    }
    return () => {
      if (focusTimeoutRef.current) {
        clearTimeout(focusTimeoutRef.current)
      }
    }
  }, [isEdit])

  const onComplete = (res: any) => {
    if (!res?.error) {
      onSave?.()
    }
  }
  const handleSave = () => {
    if (isEdit) {
      updateTrait({
        data: { id: identity, trait_key: traitKey, trait_value: traitValue },
        environmentId,
        identity,
        use_edge_identities,
      }).then(onComplete)
    } else {
      createTrait({
        data: { id: identity, trait_key: traitKey, trait_value: traitValue },
        environmentId,
        identity,
        use_edge_identities,
      }).then(onComplete)
    }
  }

  const TRAITS_ID_MAXLENGTH = Constants.forms.maxLength.TRAITS_ID

  return (
    <ProjectProvider id={`${projectId}`}>
      {({ project }: { project: any }) => (
        <form
          id='create-trait-modal'
          onSubmit={(e: FormEvent<HTMLFormElement>) => {
            e.preventDefault()
            handleSave()
          }}
        >
          <div className='modal-body'>
            <FormGroup className='mb-2'>
              <InputGroup
                ref={inputRef}
                inputProps={{
                  className: 'full-width',
                  maxLength: TRAITS_ID_MAXLENGTH,
                  name: 'traitID',
                  readOnly: isEdit,
                }}
                value={traitKey}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setTraitKey(
                    Format.enumeration
                      .set(Utils.safeParseEventValue(e))
                      .toLowerCase(),
                  )
                }
                isValid={!!traitKey && traitKey.length > 0}
                type='text'
                title={isEdit ? 'Trait ID' : 'Trait ID*'}
                placeholder='E.g. favourite_colour'
              />
            </FormGroup>
            <FormGroup className='mb-2'>
              <InputGroup
                textarea
                inputProps={{
                  className: 'full-width',
                  name: 'traitValue',
                }}
                value={traitValue}
                title='Value'
                onChange={(
                  e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
                ) =>
                  setTraitValue(
                    Utils.getTypedValue(Utils.safeParseEventValue(e)),
                  )
                }
                type='text'
                placeholder="e.g. 'big', true, 1 "
              />
            </FormGroup>

            {error && <ErrorMessage error={error} />}

            <p>
              This will {isEdit ? 'update' : 'create'} a user trait{' '}
              <strong>{traitKey || ''}</strong> for the user{' '}
              <strong>{identityName}</strong> in
              <strong>
                {' '}
                {
                  _.find(project.environments, {
                    api_key: environmentId,
                  })?.name
                }
              </strong>
            </p>

            <FormGroup className='text-muted'>
              <label>Example SDK response:</label>
              <Highlight forceExpanded className='json no-pad'>
                {JSON.stringify({
                  trait_key: traitKey,
                  trait_value: traitValue,
                })}
              </Highlight>
            </FormGroup>
          </div>
          <ModalHR />
          <div className='modal-footer'>
            <Button onClick={closeModal} theme='secondary' className='mr-2'>
              Cancel
            </Button>
            <Button
              id={isEdit ? 'update-trait-btn' : 'create-trait-btn'}
              type='submit'
              disabled={isLoading || !traitKey}
            >
              {isLoading ? 'Saving' : 'Save Trait'}
            </Button>
          </div>
        </form>
      )}
    </ProjectProvider>
  )
}

export default CreateTrait
