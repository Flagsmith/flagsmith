type StageCardProps = {
  children: React.ReactNode
}

const StageCard = ({ children }: StageCardProps) => {
  return (
    <div
      className='rounded position-relative border-1 bg-light200 bg-white p-3'
      style={{
        minHeight: '200px',
        minWidth: '280px',
        width: '280px',
      }}
    >
      {children}
    </div>
  )
}

export type { StageCardProps }
export default StageCard
