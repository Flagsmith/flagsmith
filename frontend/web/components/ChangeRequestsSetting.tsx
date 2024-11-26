import React, { FC } from 'react'
import Setting from './Setting'
import Utils from 'common/utils/utils'
import Input from './base/forms/Input'
import Button from './base/forms/Button'

type ChangeRequestsSettingType = {
  value: number | null
  onToggle: (value: number | null) => void
  onSave: () => void
  onChange: (value: number | null) => void
  isLoading: boolean
  feature: '4_EYES' | '4_EYES_PROJECT'
}

const ChangeRequestsSetting: FC<ChangeRequestsSettingType> = ({
  feature,
  isLoading,
  onChange,
  onSave,
  onToggle,
  value,
}) => {
  const has4EyesPermission = Utils.getPlansPermission('4_EYES')

  return (
    <FormGroup className='mt-4 col-md-8'>
      <Setting
        feature={feature}
        checked={has4EyesPermission && Utils.changeRequestsEnabled(value)}
        onChange={(v) => onToggle(v ? 0 : null)}
      />
      {Utils.changeRequestsEnabled(value) && has4EyesPermission && (
        <div className='mt-4'>
          <div className='mb-2'>
            <strong>Minimum number of approvals</strong>
          </div>
          <div className='d-flex align-items-center gap-2'>
            <Input
              style={{ width: 75 }}
              value={`${value}`}
              inputClassName='input'
              name='env-name'
              disabled={isLoading}
              min={0}
              onChange={(e: InputEvent) => {
                if (!Utils.safeParseEventValue(e)) return
                onChange(parseInt(Utils.safeParseEventValue(e)))
              }}
              isValid={typeof value === 'number'}
              type='number'
              placeholder='Minimum number of approvals'
            />
            <Button
              type='button'
              onClick={onSave}
              id='save-env-btn'
              className='px-4'
              disabled={isLoading}
            >
              {isLoading ? 'Saving' : 'Save'}
            </Button>
          </div>
        </div>
      )}
    </FormGroup>
  )
}

export default ChangeRequestsSetting
