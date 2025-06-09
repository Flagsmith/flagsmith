import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'

type StageArrowProps = {
  onAddStage?: () => void
  showAddStageButton?: boolean
}

const StageArrow = ({ onAddStage, showAddStageButton }: StageArrowProps) => {
  return (
    <div className='d-flex align-items-center'>
      <div className='d-flex align-items-center stage-line'>
        <div className='flex-1 line-divider' />
        {showAddStageButton && (
          <Button
            theme='icon'
            className='border-1 border-primary rounded-circle color-primary'
            onClick={onAddStage}
          >
            <Icon name='plus' fill='#6837FC' width={20} />
          </Button>
        )}
        <div className='arrow-container'>
          <div className='arrow-container__wrapper'>
            <Icon name='arrow-right' fill='#656d7b29' width={36} />
          </div>
        </div>
      </div>
    </div>
  )
}

export type { StageArrowProps }
export default StageArrow
