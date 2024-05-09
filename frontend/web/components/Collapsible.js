import React, { PureComponent } from 'react'
import Icon from './Icon'
import { IonIcon } from '@ionic/react'
import { chevronDown, chevronForward, createOutline } from 'ionicons/icons'

const cn = require('classnames')

const Collapsible = class extends PureComponent {
  static displayName = 'Collapsible'

  static propTypes = {}
  constructor(props) {
    super(props)
    this.ref = React.createRef()
  }
  handleClickOutside = (event) => {
    if (this.ref.current && !this.ref.current.contains(event.target)) {
      this.props.isProjectSelect &&
        this.props.onClickOutside &&
        this.props.onClickOutside()
    }
  }

  componentDidMount() {
    document.addEventListener('click', this.handleClickOutside, true)
  }

  componentWillUnmount() {
    document.removeEventListener('click', this.handleClickOutside, true)
  }

  render() {
    return (
      <div
        data-test={this.props['data-test']}
        className={cn('collapsible', this.props.className, {
          active: this.props.active,
        })}
        ref={this.ref}
      >
        <div className='collapsible-title mx-3' onClick={this.props.onClick}>
          <div className='flex-row'>
            <IonIcon
              className='fs-small me-2 text-muted'
              icon={
                this.props.active || this.props.isProjectSelect
                  ? chevronDown
                  : chevronForward
              }
            />

            <div>{this.props.title}</div>
          </div>
        </div>
        {this.props.active ? (
          <div className='collapsible__content'>{this.props.children}</div>
        ) : null}
      </div>
    )
  }
}

Collapsible.displayName = 'Collapsible'

// Card.propTypes = {
//     title: oneOfType([OptionalObject, OptionalString]),
//     icon: OptionalString,
//     children: OptionalNode,
// };

module.exports = Collapsible
