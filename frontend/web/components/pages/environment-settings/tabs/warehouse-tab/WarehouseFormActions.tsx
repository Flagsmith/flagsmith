import { FC } from 'react'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import Icon from 'components/icons/Icon'
import { colorIconSecondary } from 'common/theme/tokens'
import { WarehouseTestState } from './useWarehouseConnectionTest'
import {
  getButtonLabel,
  getTestFailureWarning,
  getWarehouseErrorMessage,
  STARTING_SAVE_ANYWAY,
} from './warehouseFormUtils'

type WarehouseFormActionsProps = {
  isEdit: boolean
  onCancel?: () => void
  onTest: () => void
  canTest: boolean
  canSave: boolean
  isTesting: boolean
  isSaving: boolean
  saveFailed: boolean
  testState: WarehouseTestState
  testDetail: string | null
}

const WarehouseFormActions: FC<WarehouseFormActionsProps> = ({
  canSave,
  canTest,
  isEdit,
  isSaving,
  isTesting,
  onCancel,
  onTest,
  saveFailed,
  testDetail,
  testState,
}) => (
  <>
    {saveFailed && <ErrorMessage error={getWarehouseErrorMessage(isEdit)} />}

    <div className='wh-config-form__actions'>
      {isEdit && onCancel && (
        <Button
          id='warehouse-config-cancel'
          theme='outline'
          size='small'
          onClick={onCancel}
          type='button'
        >
          Cancel
        </Button>
      )}
      <Button
        id='warehouse-config-test'
        theme='outline'
        size='small'
        type='button'
        onClick={onTest}
        disabled={!canTest || isTesting}
      >
        {isTesting ? 'Testing...' : 'Test connection'}
      </Button>
      <Button
        id='warehouse-config-save'
        theme='primary'
        size='small'
        type='submit'
        disabled={isSaving || !canSave}
      >
        {getButtonLabel(isEdit, isSaving)}
      </Button>
    </div>

    {testState === 'connected' && (
      <div className='d-flex justify-content-end'>
        <span className='fs-captionXSmall text-success'>
          Connection verified. You can now save.
        </span>
      </div>
    )}
    {testState === 'starting' && (
      <div
        role='status'
        className='d-flex flex-row flex-nowrap align-items-baseline gap-2 text-muted'
      >
        <Icon name='info' width={14} fill={colorIconSecondary} />
        <div className='d-flex flex-column'>
          <span>{testDetail}</span>
          <span>{STARTING_SAVE_ANYWAY}</span>
        </div>
      </div>
    )}
    {testState === 'errored' && (
      <div className='d-flex'>
        <ErrorMessage
          error={getTestFailureWarning(testDetail)}
          errorMessageClass='mb-0 flex-1 wh-config-form__test-error'
        />
      </div>
    )}
  </>
)

WarehouseFormActions.displayName = 'WarehouseFormActions'
export default WarehouseFormActions
