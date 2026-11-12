import { FC, ReactNode, useState } from 'react'
import Icon from 'components/icons/Icon'
import BareButton from 'components/base/forms/BareButton'
import { colorIconSecondary } from 'common/theme/tokens'

type WarehouseSetupStepsProps = {
  configure: ReactNode
  connectDescription: string
  children: ReactNode
}

const WarehouseSetupSteps: FC<WarehouseSetupStepsProps> = ({
  children,
  configure,
  connectDescription,
}) => {
  const [configureExpanded, setConfigureExpanded] = useState(true)

  return (
    <div className='warehouse-setup__steps'>
      <div className='warehouse-setup__step'>
        <div className='warehouse-setup__step-rail'>
          <div className='warehouse-setup__step-marker'>1</div>
          <div className='warehouse-setup__step-connector' />
        </div>
        <div className='warehouse-setup__step-content'>
          <BareButton
            className='warehouse-setup__step-toggle mb-2'
            aria-expanded={configureExpanded}
            onClick={() => setConfigureExpanded(!configureExpanded)}
          >
            <h6 className='mb-0'>
              Configure your warehouse for experimentation
            </h6>
            <Icon
              name={configureExpanded ? 'chevron-up' : 'chevron-down'}
              width={22}
              fill={colorIconSecondary}
            />
          </BareButton>
          {configureExpanded && configure}
        </div>
      </div>
      <div className='warehouse-setup__step'>
        <div className='warehouse-setup__step-rail'>
          <div className='warehouse-setup__step-marker'>2</div>
        </div>
        <div className='warehouse-setup__step-content'>
          <h6 className='mb-2'>Connect your warehouse</h6>
          <p className='text-muted mb-3'>{connectDescription}</p>
          {children}
        </div>
      </div>
    </div>
  )
}

WarehouseSetupSteps.displayName = 'WarehouseSetupSteps'
export default WarehouseSetupSteps
