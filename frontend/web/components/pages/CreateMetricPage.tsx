import { FC, useState } from 'react'
import { useHistory } from 'react-router-dom'
import Utils from 'common/utils/utils'
import { useRouteContext } from 'components/providers/RouteContext'
import { useCreateMetricMutation } from 'common/services/useMetric'
import PageTitle from 'components/PageTitle'
import CreateMetricForm from 'components/experiments/CreateMetricForm'
import {
  buildMetricPayload,
  MetricFormState,
} from 'components/experiments/CreateMetricForm/utils'

const CreateMetricPage: FC = () => {
  const { environmentId, projectId } = useRouteContext()
  const history = useHistory()
  const [formKey, setFormKey] = useState(0)
  const [createMetric, { isLoading: isSaving }] = useCreateMetricMutation()

  if (!environmentId || !projectId) return null

  if (!Utils.getFlagsmithHasFeature('experiment_metrics')) {
    history.replace(
      `/project/${projectId}/environment/${environmentId}/features`,
    )
    return null
  }

  const resetForm = () => setFormKey((key) => key + 1)

  const handleSubmit = async (state: MetricFormState) => {
    try {
      await createMetric({
        body: buildMetricPayload(state),
        environmentId,
      }).unwrap()
      toast('Metric created successfully')
      resetForm()
    } catch {
      toast('Failed to create metric', 'danger')
    }
  }

  return (
    <div data-test='create-metric-page' className='app-container container'>
      <PageTitle title='Metrics' />
      <CreateMetricForm
        key={formKey}
        isSaving={isSaving}
        onCancel={resetForm}
        onSubmit={handleSubmit}
      />
    </div>
  )
}

CreateMetricPage.displayName = 'CreateMetricPage'
export default CreateMetricPage
