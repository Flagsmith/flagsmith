import { FC } from 'react'
import Banner from 'components/base/Banner'
import { PrerequisiteRow } from './PrerequisitesTable'

type DependencyStatusHeaderProps = {
  environmentName: string
  rows: PrerequisiteRow[]
}

// "1 of 1" and "9 of 9" both carry one fact, not two, so neither gets a ratio.
const describe = (offCount: number, total: number): string => {
  if (total === 1) {
    return 'Its prerequisite is off'
  }
  if (offCount === total) {
    return `All ${total} prerequisites are off`
  }
  return `${offCount} of ${total} prerequisites are off`
}

// Only rendered when the flag is held off, so there is always something to act
// on. A flag serving its own value needs no announcement: the table's ticks
// already say so.
const DependencyStatusHeader: FC<DependencyStatusHeaderProps> = ({
  environmentName,
  rows,
}) => {
  // The verdict only counts edges whose rule we can read. The count beside it
  // is about on and off, which is known for every row either way.
  const isBlocked = rows.some((row) => row.isMet === false)
  if (!isBlocked) {
    return null
  }

  const offCount = rows.filter((row) => !row.isEnabled).length

  return (
    <Banner
      type='warning'
      className='mb-3'
      title={`Serving off in ${environmentName}`}
    >
      {describe(offCount, rows.length)}
    </Banner>
  )
}

export default DependencyStatusHeader
