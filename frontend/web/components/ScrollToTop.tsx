import { FC, useEffect } from 'react'
import { withRouter } from 'react-router-dom'
import { RouteComponentProps } from 'react-router'

type ScrollToTopType = RouteComponentProps & {}

const ScrollToTop: FC<ScrollToTopType> = (props) => {
  const pathname = props.location.pathname
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return null
}

export default withRouter(ScrollToTop)
