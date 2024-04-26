import cn from 'classnames'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

const themeClassNames = {
  danger: 'alert-danger',
  info: 'alert-info',
  success: 'alert',
  warning: 'alert-warning',
}

const Message = class extends React.Component {
  static displayName = 'Message'

  componentDidMount() {
    setTimeout(this.props.remove, this.props.expiry)
  }

  render() {
    const className = cn(
      {
        'alert': true,
        'removing out': this.props.isRemoving,
        'show': !this.props.isRemoving,
        'toast-message': true,
      },
      themeClassNames[this.props.theme],
    )

    return (
      <div className={className}>
        <Row space className={'flex-nowrap'}>
          <span>{this.props.children}</span>
          <a onClick={this.props.remove}>
            <span className='icon'>
              <IonIcon icon={close} style={{ fontSize: '13px' }} />
            </span>
          </a>
        </Row>
      </div>
    )
  }
}

Message.defaultProps = {
  expiry: 5000,
  theme: 'success',
}

Message.propTypes = {
  children: OptionalNode,
  content: OptionalNode,
  expiry: OptionalNumber,
  isRemoving: OptionalBool,
  remove: RequiredFunc,
  theme: OptionalString,
}

module.exports = Message

const Toast = class extends React.Component {
  static displayName = 'ToastMessages'

  constructor(props, context) {
    super(props, context)
    this.state = { messages: [] }
    window.toast = this.toast
  }

  toast = (content, theme, expiry) => {
    const { messages } = this.state

    // Ignore duplicate messages
    if (messages[0]?.content === content) {
      return
    }
    const id = Utils.GUID()
    messages.unshift({ content, expiry: E2E ? 1000 : expiry, id, theme })
    this.setState({ messages })
  }

  remove = (id) => {
    const index = _.findIndex(this.state.messages, { id })
    const messages = this.state.messages

    if (index > -1) {
      messages[index].isRemoving = true
      setTimeout(() => {
        const index = _.findIndex(this.state.messages, { id })
        const messages = this.state.messages
        messages.splice(index, 1)
        this.setState({ messages })
      }, 500)
      this.setState({ messages })
    }
  }

  render() {
    return (
      <div className='toast-messages'>
        {this.state.messages.map((message) => (
          <Message
            key={message.id}
            isRemoving={message.isRemoving}
            remove={() => this.remove(message.id)}
            expiry={message.expiry}
            theme={message.theme}
          >
            {message.content}
          </Message>
        ))}
      </div>
    )
  }
}
module.exports = Toast
