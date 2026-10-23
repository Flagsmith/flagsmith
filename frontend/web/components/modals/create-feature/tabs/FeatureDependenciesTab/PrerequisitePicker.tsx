import { FC } from 'react'
import { ProjectFlag } from 'common/types/responses'
import FeatureSelect from 'components/FeatureSelect'

type PrerequisitePickerProps = {
  disabled: boolean
  environmentId: string
  featureId: number
  existingPrerequisiteIds: number[]
  projectId: number
  onChange: (feature: ProjectFlag) => void
}

const PrerequisitePicker: FC<PrerequisitePickerProps> = ({
  disabled,
  environmentId,
  existingPrerequisiteIds,
  featureId,
  onChange,
  projectId,
}) => (
  <FeatureSelect
    projectId={projectId}
    environmentId={environmentId}
    disabled={disabled}
    placeholder='Add a prerequisite flag...'
    // The API refuses both of these, so keep them out of the list.
    ignore={[featureId, ...existingPrerequisiteIds]}
    onChange={onChange}
  />
)

export default PrerequisitePicker
