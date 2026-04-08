import './project/polyfil'
import './project/libs'
import './project/api'
import './project/project-components'
import './styles/styles.scss'
import { BrowserRouter as Router } from 'react-router-dom'
import { createBrowserHistory } from 'history'
import { createRoot } from 'react-dom/client'
import ToastMessages from './project/toast'
import routes from './routes'
import Utils from 'common/utils/utils'
import Project from 'common/project'
import AccountStore from 'common/stores/account-store'
import data from 'common/data/base/_data'
import {
  openModal,
  openModal2,
  openConfirm,
} from './components/modals/base/Modal'

window.Utils = Utils
window.openModal = openModal
window.openModal2 = openModal2
window.openConfirm = openConfirm

const rootElement = document.getElementById('app')

const params = Utils.fromParam()

if (params.token) {
  API.setCookie('t', params.token)
  document.location = document.location.origin
}

// Render the React application to the DOM
const res = API.getCookie('t')

const event = API.getEvent()
if (event) {
  try {
    data
      .post('/api/event', JSON.parse(event))
      .catch(() => {})
      .finally(() => {
        API.setEvent('')
      })
  } catch (e) {}
}

const isInvite = document.location.href.includes('invite')
const isOauth =
  document.location.href.includes('/oauth') &&
  !document.location.pathname.startsWith('/oauth/authorize')
if (res && !isInvite && !isOauth) {
  AppActions.setToken(res)
}

function isPublicURL() {
  const pathname = document.location.pathname

  // /oauth/authorize requires auth (consent screen), but /oauth/:type (callbacks) is public.
  if (pathname.startsWith('/oauth/authorize')) {
    return false
  }

  const publicPaths = [
    '/',
    '/404',
    '/home',
    '/password-reset',
    '/maintenance',
    '/github-setup',
    '/oauth',
    '/register',
    '/saml',
    '/signup',
    '/login',
  ]

  return publicPaths.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`),
  )
}

setTimeout(() => {
  const browserHistory = createBrowserHistory({
    basename: Project.basename || '',
  })

  // redirect before login
  if (!isPublicURL() && !AccountStore.getUser()) {
    API.setRedirect(
      document.location.pathname + (document.location.search || ''),
    )
    browserHistory.push(
      `/?redirect=${encodeURIComponent(
        document.location.pathname + (document.location.search || ''),
      )}`,
    )
  }

  const root = createRoot(rootElement)
  root.render(<Router basename={Project.basename || ''}>{routes}</Router>)
}, 1)

// Setup for toast messages
const toastRoot = createRoot(document.getElementById('toast'))
toastRoot.render(<ToastMessages />)

if (E2E) {
  document.body.classList.add('disable-transitions')
}
