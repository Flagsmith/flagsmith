import { SyntheticEvent, useEffect, useMemo, useState } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import { PipelineStage as PipelineStageType } from 'common/types/responses'

type DraftStageType = Omit<PipelineStageType, 'id' | 'pipeline'>

const TRIGGER_OPTIONS = [
  { label: 'When flag is added to this stage', value: 'flag-added-to-stage' },
  { label: 'Wait for approval', value: 'wait-for-approval' },
  { label: 'Wait a set amount of time', value: 'wait-for-time' },
  {
    description: 'coming soon!',
    isDisabled: true,
    label: 'When change request is approved',
    value: 'change-request-approved',
  },
]

const FLAG_ACTIONS = {
  'change-request-approved': [],
  'flag-added-to-stage': [
    { label: 'Enable flag for everyone', value: 'enabled-for-everyone' },
    { label: 'Enable flag for a segment', value: 'enabled-for-segment' },
    {
      description: 'coming soon!',
      isDisabled: true,
      label: 'Start a progressive rollout',
      value: 'start-progressive-rollout',
    },
  ],
  'wait-for-approval': [],
  'wait-for-time': [],
}

const PipelineStage = ({
  onChange,
  projectId,
  stageData,
}: {
  stageData: DraftStageType
  onChange: (stageData: DraftStageType) => void
  projectId: string
}) => {
  const [searchInput, setSearchInput] = useState('')
  const [selectedAction, setSelectedAction] = useState<{
    label: string
    value: string
  }>({ label: 'Select an action', value: '' })
  const [selectedTrigger, setSelectedTrigger] = useState<{
    label: string
    value: string
  }>(TRIGGER_OPTIONS[0])

  const { data: environmentsData, isLoading: isEnvironmentsLoading } =
    useGetEnvironmentsQuery(
      {
        projectId,
      },
      { skip: !projectId },
    )

  const { data: segments, isLoading: isSegmentsLoading } = useGetSegmentsQuery(
    {
      include_feature_specific: true,
      page_size: 1000,
      projectId,
    },
    { skip: !projectId || selectedAction?.value !== 'enabled-for-segment' },
  )

  const segmentOptions = useMemo(() => {
    return segments?.results?.map((segment) => ({
      label: segment.name,
      value: segment.id,
    }))
  }, [segments])

  const environmentOptions = useMemo(() => {
    return environmentsData?.results?.map((environment) => ({
      label: environment.name,
      value: environment.id,
    }))
  }, [environmentsData])

  const handleOnChange = (fieldName: string, value: string | number) => {
    onChange({ ...stageData, [fieldName]: value })
  }

  useEffect(() => {
    if (!stageData.environment && environmentOptions?.length) {
      handleOnChange('environmentId', environmentOptions?.[0].value)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stageData.environment, environmentOptions])

  return (
    <div className='p-3 border-1 rounded' style={{ minWidth: '360px' }}>
      <FormGroup>
        <InputGroup
          title='Stage Name'
          inputProps={{ className: 'full-width' }}
          value={stageData.name}
          onChange={(e: SyntheticEvent<HTMLInputElement>) => {
            handleOnChange('name', e.currentTarget.value)
          }}
        />
      </FormGroup>
      <FormGroup>
        <InputGroup
          title='Environment'
          component={
            <Select
              value={Utils.toSelectedValue(
                stageData.environment,
                environmentOptions,
                environmentOptions?.[0],
              )}
              isDisabled={isEnvironmentsLoading}
              isLoading={isEnvironmentsLoading}
              inputValue={searchInput}
              onInputChange={setSearchInput}
              options={environmentOptions}
              onChange={(option: { value: number; label: string }) =>
                handleOnChange('environmentId', option.value)
              }
            />
          }
        />
      </FormGroup>
      <FormGroup>
        <InputGroup
          title='Trigger'
          component={
            <Select
              isDisabled={isEnvironmentsLoading}
              isLoading={isEnvironmentsLoading}
              value={selectedTrigger}
              options={TRIGGER_OPTIONS}
              onChange={(option: { value: string; label: string }) =>
                setSelectedTrigger(option)
              }
            />
          }
        />
      </FormGroup>
      <Row>
        <div className='flex-1 and-divider__line' />
        <div className='mx-2'>Then</div>
        <div className='flex-1 and-divider__line' />
      </Row>
      <FormGroup>
        <InputGroup
          title='Flag Action'
          component={
            <Select
              value={selectedAction}
              options={
                selectedTrigger
                  ? FLAG_ACTIONS[
                      selectedTrigger.value as keyof typeof FLAG_ACTIONS
                    ]
                  : []
              }
              onChange={(option: { value: string; label: string }) => {
                setSelectedAction(option)
                if (option.value === 'enabled-for-everyone') {
                  handleOnChange('segment', 'all')
                }
              }}
            />
          }
        />
      </FormGroup>
      {/* {selectedAction?.value === 'enabled-for-segment' && (
        <FormGroup className='pl-4'>
          <InputGroup
            title='Segment'
            component={
              <Select
                isDisabled={isSegmentsLoading}
                isLoading={isSegmentsLoading}
                value={Utils.toSelectedValue(
                  stageData.segment,
                  segmentOptions,
                  { label: 'Select a segment', value: '' },
                )}
                options={segmentOptions}
                onChange={(option: { value: number; label: string }) =>
                  handleOnChange('segment', option.value)
                }
              />
            }
          />
        </FormGroup>
      )} */}
    </div>
  )
}

export type { DraftStageType }
export default PipelineStage
