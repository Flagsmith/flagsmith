import React from 'react'
import Icon from './icons/Icon'
import Tooltip from './Tooltip'
import { colorIconSecondary } from 'common/theme/tokens'

let prom
class _Headway extends React.Component {
  state = {
    ready: false,
  }
  componentDidMount() {
    try {
      if (Project.headway) {
        if (!prom) {
          prom = Utils.loadScriptPromise('https://cdn.headwayapp.co/widget.js')
        }
        prom.then(() => {
          this.setState({ ready: true }, () => {
            Headway.init({
              account: Project.headway,
              enabled: true,
              selector: '#headway',
            })
          })
        })
      }
    } catch (e) {}
  }

  render() {
    if (!Project.headway || !this.state.ready) {
      return null
    }
    return (
      <Tooltip
        place='bottom'
        title={
          <Row
            onClick={() => {
              Headway.show()
            }}
            className={this.props.className}
          >
            <Icon name='bell' width={20} fill={colorIconSecondary} />
            <span id='headway'>
              <span />
            </span>
          </Row>
        }
      >
        Updates
      </Tooltip>
    )
  }
}

export default _Headway
