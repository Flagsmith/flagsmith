import Icon from 'components/Icon'

type DerivedTagProps = {
  name: string
  type: 'group' | 'role'
}

const DerivedTag = ({ name, type }: DerivedTagProps) => {
  return (
    <div className='chip me-2 chip--xs bg-primary text-white'>
      <div className='mr-1'>
        <Icon
          fill='white'
          width={12}
          height={12}
          name={type === 'group' ? 'people' : 'award'}
        />
      </div>
      {name}
    </div>
  )
}

export type { DerivedTagProps }
export default DerivedTag
