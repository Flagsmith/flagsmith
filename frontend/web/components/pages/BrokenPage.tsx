import { FC } from 'react' // we need this to make JSX compile

type BrokenPageType = {}

const BrokenPage: FC<BrokenPageType> = ({}) => {
  throw new Error('An example error')
  return <></>
}

export default BrokenPage
