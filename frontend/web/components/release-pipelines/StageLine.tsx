import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'

type StageLineProps = {
  onAddStage: () => void
  showAddStageButton: boolean
}

const StageLine = ({ onAddStage, showAddStageButton }: StageLineProps) => {
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

      {showAddStageButton && (
        <div className='d-flex align-items-center p-2 border-1 rounded border-primary '>
          <Icon width={30} name='checkmark-circle' fill='#27AB95' />
          Launched
        </div>
      )}
    </div>
  )
}

export type { StageLineProps }
export default StageLine
