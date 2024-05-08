import { PureComponent } from 'react'
import Select from 'react-select'
import Button from 'components/base/forms/Button'
import Paging from 'components/Paging'
import ToggleChip from 'components/ToggleChip'
import Input from 'components/base/forms/Input'
import InputGroup from 'components/base/forms/InputGroup'
import PanelSearch from 'components/PanelSearch'
import AccountStore from 'common/stores/account-store'
import Tooltip from 'components/Tooltip'
import ProjectProvider from 'common/providers/ProjectProvider'
import AccountProvider from 'common/providers/AccountProvider'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import Panel from 'components/base/grid/Panel'

window.AppActions = require('../../common/dispatcher/app-actions')
window.Actions = require('../../common/dispatcher/action-constants')
window.ES6Component = require('../../common/ES6Component')

window.IdentityProvider = require('../../common/providers/IdentityProvider')
window.IdentityProvider = require('../../common/providers/IdentityProvider')
window.AccountProvider = AccountProvider
window.AccountStore = AccountStore
window.FeatureListProvider = require('../../common/providers/FeatureListProvider')
window.OrganisationProvider = OrganisationProvider
window.ProjectProvider = ProjectProvider

window.Paging = Paging

// Useful components
window.Row = require('../components/base/grid/Row')
window.Flex = require('../components/base/grid/Flex')
window.Column = require('../components/base/grid/Column')
window.InputGroup = InputGroup
window.Input = Input
window.Button = Button
window.FormGroup = require('../components/base/grid/FormGroup')
window.Panel = Panel
window.FormGroup = require('../components/base/grid/FormGroup')

window.PanelSearch = PanelSearch
window.CodeHelp = require('../components/CodeHelp')

// Useful for components used all the time within a project
window.Loader = class extends PureComponent {
  static displayName = 'Loader'

  render() {
    return (
      <svg
        className='loader'
        version='1.1'
        id='loader-1'
        x='0px'
        y='0px'
        width='40px'
        height='40px'
        viewBox='0 0 50 50'
        style={{ enableBackground: '0 0 50 50' }}
      >
        <path
          fill='#6633ff'
          d='M25.251,6.461c-10.318,0-18.683,8.365-18.683,18.683h4.068c0-8.071,6.543-14.615,14.615-14.615V6.461z'
        >
          <animateTransform
            attributeType='xml'
            attributeName='transform'
            type='rotate'
            from='0 25 25'
            to='360 25 25'
            dur='0.6s'
            repeatCount='indefinite'
          />
        </path>
      </svg>
    )
  }
}

window.Tooltip = Tooltip

global.ToggleChip = ToggleChip
global.Select = class extends PureComponent {
  static displayName = 'Select'

  render() {
    const props = this.props
    return E2E ? (
      <div>
        <input
          type='text'
          ref={(input) => (this.input = input)}
          value={props.value && props.value.value}
          onChange={(e) =>
            props.onChange({ value: Utils.safeParseEventValue(e) })
          }
          id={props.id}
          data-test={props['data-test']}
        />
        {this.props.options &&
          this.props.options.map((option, index) => (
            <a
              key={index}
              onClick={() => props.onChange(option)}
              data-test={
                this.props.dataTest
                  ? this.props.dataTest(option)
                  : `${props['data-test']}-option-${index}`
              }
            >
              .
            </a>
          ))}
      </div>
    ) : (
      <Select
        className={`react-select ${props.size ? props.size : ''}`}
        classNamePrefix='react-select'
        {...props}
      />
    )
  }
}
