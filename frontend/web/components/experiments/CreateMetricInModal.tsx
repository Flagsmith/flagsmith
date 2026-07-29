import { FC } from 'react'
import { Metric } from 'common/types/responses'
import { useCreateMetricMutation } from 'common/services/useMetric'
import Utils from 'common/utils/utils'
import CreateMetricForm from './CreateMetricForm'
import {
  buildMetricPayload,
  DEFAULT_METRIC_DEFINITION_VERSION,
  MetricFormState,
} from './CreateMetricForm/utils'

type CreateMetricInModalProps = {
  environmentId: string
  onClose: () => void
  onCreated: (metric: Metric) => void
}

const CreateMetricInModal: FC<CreateMetricInModalProps> = ({
  environmentId,
  onClose,
  onCreated,
}) => {
  const [createMetric, { isLoading: isSaving }] = useCreateMetricMutation()
  const version =
    Number(Utils.getFlagsmithValue('experiment_metrics')) ||
    DEFAULT_METRIC_DEFINITION_VERSION

  const handleSubmit = async (state: MetricFormState) => {
    try {
      const metric = await createMetric({
        body: buildMetricPayload(state, version),
        environmentId,
      }).unwrap()
      toast('Metric created successfully')
      onClose()
      onCreated(metric)
    } catch {
      toast('Failed to create metric', 'danger')
    }
  }

  return (
    <CreateMetricForm
      isSaving={isSaving}
      onCancel={onClose}
      onSubmit={handleSubmit}
    />
  )
}

export default CreateMetricInModal
