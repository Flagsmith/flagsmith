import {FC, useEffect} from 'react'
import ErrorMessage from "components/ErrorMessage"; // we need this to make JSX compile

type BrokenPageType = {}

const BrokenPage: FC<BrokenPageType> = ({}) => {
  useEffect(()=>{
    setTimeout(()=>{
      throw new Error("An example error")
    },0)
  },[])
  return  <div
      data-test='features-page'
      id='features-page'
      className='app-container container'
  >
    <ErrorMessage error={"An example error"}/>
  </div>
}

export default BrokenPage
