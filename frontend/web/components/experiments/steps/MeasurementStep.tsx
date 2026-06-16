import { FC, useState } from 'react'
import { ExpectedDirection, Metric } from 'common/types/responses'
import ContentCard from 'components/base/grid/ContentCard'
import CenteredModal from 'components/base/CenteredModal'
import CreateMetricInModal from 'components/experiments/CreateMetricInModal'
import MetricSelectList from 'components/experiments/MetricSelectList'
import {
  EXPECTED_DIRECTION_OPTIONS,
  ExpectedDirectionOption,
} from 'components/experiments/constants'

type MeasurementStepProps = {
  environmentId: string
  selectedMetric: Metric | null
  expectedDirection: ExpectedDirection | null
  onMetricSelect: (metric: Metric) => void
  onExpectedDirectionChange: (direction: ExpectedDirection) => void
}

const MeasurementStep: FC<MeasurementStepProps> = ({
  environmentId,
  expectedDirection,
  onExpectedDirectionChange,
  onMetricSelect,
  selectedMetric,
}) => {
  const [isCreateMetricOpen, setIsCreateMetricOpen] = useState(false)

  return (
    <div className='d-flex flex-column gap-4'>
      <ContentCard
        title='Metrics'
        description='Select the primary metric this experiment will be judged on.'
      >
        <MetricSelectList
          environmentId={environmentId}
          selectedMetric={selectedMetric}
          onSelect={onMetricSelect}
          onCreateClick={() => setIsCreateMetricOpen(true)}
        />

        {selectedMetric && (
          <div className='wizard-field'>
            <label className='wizard-field__label'>Expected direction</label>
            <Select
              value={
                EXPECTED_DIRECTION_OPTIONS.find(
                  (option) => option.value === expectedDirection,
                ) ?? null
              }
              options={EXPECTED_DIRECTION_OPTIONS}
              onChange={(option: ExpectedDirectionOption | null) => {
                if (option) onExpectedDirectionChange(option.value)
              }}
              placeholder='Select an expected direction...'
              isClearable={false}
            />
            <span className='wizard-field__hint'>
              How you expect the primary metric to move if the hypothesis is
              true.
            </span>
          </div>
        )}
      </ContentCard>

      <CenteredModal
        isOpen={isCreateMetricOpen}
        title='Create Metric'
        onClose={() => setIsCreateMetricOpen(false)}
      >
        <CreateMetricInModal
          environmentId={environmentId}
          onClose={() => setIsCreateMetricOpen(false)}
          onCreated={onMetricSelect}
        />
      </CenteredModal>
    </div>
  )
}

export default MeasurementStep
