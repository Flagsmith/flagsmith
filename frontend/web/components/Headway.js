import React from 'react'
import Button from './base/forms/Button'
import Icon from './Icon'
import Tooltip from './Tooltip'

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
          <Row className={this.props.className}>
            <Button
              onClick={() => {
                Headway.show()
              }}
              className='btn-with-icon'
              size='small'
            >
              <Icon name='bell' width={20} fill='#9DA4AE' />
            </Button>
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
