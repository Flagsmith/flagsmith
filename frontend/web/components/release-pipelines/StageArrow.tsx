import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'

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
          <IconButton
            variant='outline'
            size='small'
            aria-label='Add stage'
            className='rounded-circle'
            onClick={onAddStage}
          >
            <Icon width={16} name='plus' />
          </IconButton>
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

export default StageArrow
