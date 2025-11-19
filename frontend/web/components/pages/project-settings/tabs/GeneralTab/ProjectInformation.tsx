import React from 'react'
import classNames from 'classnames'
import Icon from 'components/Icon'
import Tooltip from 'components/Tooltip'
import PlanBasedBanner from 'components/PlanBasedAccess'
import Utils from 'common/utils/utils'

type ProjectInformationProps = {
  name: string
  staleFlagsLimitDays: number | undefined
  onNameChange: (name: string) => void
  onStaleFlagsChange: (days: number) => void
  onSubmit: () => void
  isSaving: boolean
}

export const ProjectInformation = ({
  isSaving,
  name,
  onNameChange,
  onStaleFlagsChange,
  onSubmit,
  staleFlagsLimitDays,
}: ProjectInformationProps) => {
  const hasStaleFlagsPermission = Utils.getPlansPermission('STALE_FLAGS')
  const hasVersioning = Utils.getFlagsmithHasFeature('feature_versioning')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit()
  }

  return (
    <FormGroup>
      <form onSubmit={handleSubmit}>
        <Row className='align-items-start'>
          <Flex className='ml-0'>
            <Input
              value={name}
              inputClassName='full-width'
              name='proj-name'
              onChange={(e: InputEvent) =>
                onNameChange(Utils.safeParseEventValue(e))
              }
              isValid={!!name && name.length > 0}
              type='text'
              title={<label>Project Name</label>}
              placeholder='My Project Name'
            />
          </Flex>
        </Row>

        {hasVersioning && (
          <>
            <div className='d-flex mt-4 gap-2 align-items-center'>
              <Tooltip
                title={
                  <>
                    <label className='mb-0'>Stale Flag Detection </label>
                    <Icon name='info-outlined' />
                  </>
                }
              >
                {`If no changes have been made to a feature in any environment within this threshold the feature will be tagged as stale. You will need to enable feature versioning in your environments for stale features to be detected.`}
              </Tooltip>
              <PlanBasedBanner feature={'STALE_FLAGS'} theme={'badge'} />
            </div>
            <div className='d-flex align-items-center gap-2'>
              <label
                className={classNames('mb-0', {
                  'opacity-50': !hasStaleFlagsPermission,
                })}
              >
                Mark as stale after
              </label>
              <div style={{ width: 80 }} className='ml-0'>
                <Input
                  disabled={!hasStaleFlagsPermission}
                  value={staleFlagsLimitDays}
                  onChange={(e: InputEvent) =>
                    onStaleFlagsChange(
                      parseInt(Utils.safeParseEventValue(e)) || 0,
                    )
                  }
                  isValid={!!staleFlagsLimitDays}
                  type='number'
                  placeholder='Number of Days'
                />
              </div>
              <label
                className={classNames('mb-0', {
                  'opacity-50': !hasStaleFlagsPermission,
                })}
              >
                Days
              </label>
            </div>
            {!hasStaleFlagsPermission && (
              <PlanBasedBanner
                className='mt-2'
                feature={'STALE_FLAGS'}
                theme={'description'}
              />
            )}
          </>
        )}

        <div className='text-right'>
          <Button
            type='submit'
            id='save-proj-btn'
            disabled={isSaving || !name}
            className='ml-3'
          >
            {isSaving ? 'Updating' : 'Update'}
          </Button>
        </div>
      </form>
    </FormGroup>
  )
}
