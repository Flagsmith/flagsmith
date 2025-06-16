import Icon from 'components/Icon'
import { FC } from 'react'

interface LabelWithTooltipProps {
  label: string
  tooltip?: string
}

const LabelWithTooltip: FC<LabelWithTooltipProps> = ({ label, tooltip }) => {
  return (
    <>
      {label}{' '}
      {tooltip && (
        <Tooltip
          title={<Icon name='info-outlined' width={12} height={12} />}
          place='top'
          titleClassName='cursor-pointer'
        >
          {tooltip}
        </Tooltip>
      )}
    </>
  )
}

export default LabelWithTooltip
