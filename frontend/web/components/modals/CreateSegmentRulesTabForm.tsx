import React from 'react'
import InfoMessage from 'components/InfoMessage'
import Input from 'components/base/forms/Input'
import InputGroup from 'components/base/forms/InputGroup'
import Switch from 'components/Switch'
import Button from 'components/base/forms/Button'
import Format from 'common/utils/format'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import JSONReference from 'components/JSONReference'
import { Segment } from 'common/types/responses'
import ChangeRequestModal from './ChangeRequestModal'

type DefaultSegmentType = Omit<Segment, 'id' | 'project' | 'uuid'> & {
  id?: number
  uuid?: string
  project?: number
}

interface CreateSegmentRulesTabFormProps {
  save: (e: React.FormEvent<HTMLFormElement>) => void
  condensed?: boolean
  segmentsLimitAlert: { percentage: number }
  name: string
  is4Eyes?: boolean
  onCreateChangeRequest: (changeRequestData: {
    approvals: []
    description: string
    title: string
  }) => void
  setName: (name: string) => void
  setValueChanged: (value: boolean) => void
  description: string
  setDescription: (description: string) => void
  identity?: boolean
  readOnly?: boolean
  showDescriptions: boolean
  setShowDescriptions: (show: boolean) => void
  allWarnings: string[]
  rulesEl: React.ReactNode
  isEdit: boolean
  segment: Segment | DefaultSegmentType
  isSaving: boolean
  isValid: boolean
  isLimitReached: boolean
  onCancel?: () => void
}

const CreateSegmentRulesTabForm: React.FC<CreateSegmentRulesTabFormProps> = ({
  allWarnings,
  condensed,
  description,
  identity,
  is4Eyes,
  isEdit,
  isLimitReached,
  isSaving,
  isValid,
  name,
  onCancel,
  onCreateChangeRequest,
  readOnly,
  rulesEl,
  save,
  segment,
  segmentsLimitAlert,
  setDescription,
  setName,
  setShowDescriptions,
  setValueChanged,
  showDescriptions,
}) => {
  const SEGMENT_ID_MAXLENGTH = Constants.forms.maxLength.SEGMENT_ID
  return (
    <form id='create-segment-modal' onSubmit={save}>
      {!condensed && (
        <div className='mt-3'>
          <InfoMessage collapseId={'value-type-conversions'}>
            Learn more about rule and trait value type conversions{' '}
            <a href='https://docs.flagsmith.com/basic-features/segments#rule-typing'>
              here
            </a>
            .
          </InfoMessage>
          {segmentsLimitAlert.percentage &&
            Utils.displayLimitAlert('segments', segmentsLimitAlert.percentage)}
        </div>
      )}

      <div className='mb-3'>
        <label htmlFor='segmentID'>Name*</label>
        <Flex>
          <Input
            data-test='segmentID'
            name='id'
            id='segmentID'
            maxLength={SEGMENT_ID_MAXLENGTH}
            value={name}
            onChange={(e: InputEvent) => {
              setValueChanged(true)
              setName(
                Format.enumeration
                  .set(Utils.safeParseEventValue(e))
                  .toLowerCase(),
              )
            }}
            isValid={name && name.length}
            type='text'
            placeholder='E.g. power_users'
          />
        </Flex>
      </div>
      {!condensed && (
        <InputGroup
          className='mb-3'
          value={description}
          inputProps={{
            className: 'full-width',
            name: 'featureDesc',
            readOnly: !!identity || readOnly,
          }}
          onChange={(e: InputEvent) => {
            setValueChanged(true)
            setDescription(Utils.safeParseEventValue(e))
          }}
          isValid={name && name.length}
          type='text'
          title='Description'
          placeholder="e.g. 'People who have spent over $100' "
        />
      )}

      <div className='form-group '>
        <Row className='mb-3'>
          <Switch
            checked={showDescriptions}
            onChange={() => {
              setShowDescriptions(!showDescriptions)
            }}
            className={'ml-0'}
          />
          <span
            style={{ fontWeight: 'normal', marginLeft: '12px' }}
            className='mb-0 fs-small text-dark'
          >
            Show condition descriptions
          </span>
        </Row>
        <Flex className='mb-3'>
          <label className='cols-sm-2 control-label mb-1'>
            Include users when all of the following rules apply:
          </label>
          <span className='fs-caption text-faint'>
            Note: Trait names are case sensitive
          </span>
        </Flex>
        {allWarnings?.map((warning, i) => (
          <InfoMessage key={i}>
            <div dangerouslySetInnerHTML={{ __html: warning }} />
          </InfoMessage>
        ))}
        {rulesEl}
      </div>

      {isEdit && <JSONReference title={'Segment'} json={segment} />}
      {readOnly ? (
        <div className='text-right'>
          <Tooltip
            title={
              <Button
                disabled
                data-test='show-create-feature-btn'
                id='show-create-feature-btn'
              >
                Update Segment
              </Button>
            }
            place='left'
          >
            {Constants.projectPermissions('Admin')}
          </Tooltip>
        </div>
      ) : (
        <div className='text-right' style={{ marginTop: '32px' }}>
          <Row className='justify-content-end'>
            {condensed && (
              <Button
                theme='secondary'
                type='button'
                onClick={onCancel}
                className='mr-2'
              >
                Cancel
              </Button>
            )}
            {isEdit ? (
              is4Eyes ? (
                <Button
                  onClick={() => {
                    openModal2(
                      'New Change Request',
                      <ChangeRequestModal
                        showAssignees={is4Eyes}
                        hideSchedule
                        onSave={onCreateChangeRequest}
                      />,
                    )
                  }}
                  data-test='update-segment'
                  id='update-feature-btn'
                  disabled={isSaving || !name || !isValid}
                >
                  {isSaving ? 'Creating' : 'Create Change Request'}
                </Button>
              ) : (
                <Button
                  type='submit'
                  data-test='update-segment'
                  id='update-feature-btn'
                  disabled={isSaving || !name || !isValid}
                >
                  {isSaving ? 'Creating' : 'Update Segment'}
                </Button>
              )
            ) : (
              <Button
                disabled={isSaving || !name || !isValid || isLimitReached}
                type='submit'
                data-test='create-segment'
                id='create-feature-btn'
              >
                {isSaving ? 'Creating' : 'Create Segment'}
              </Button>
            )}
          </Row>
        </div>
      )}
    </form>
  )
}

export default CreateSegmentRulesTabForm
