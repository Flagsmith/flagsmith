import cn from 'classnames'

const Message = class extends React.Component {
  static displayName = 'Message'

  componentDidMount() {
    if (this.props.expiry !== 0) {
      setTimeout(this.props.remove, this.props.expiry)
    }
  }

  render() {
    const toastStyle =
      this.props.position === 'center' ? 'toast-warning ' : 'toast-message'

    const className = cn({
      'alert alert-warning fade': true,
      'removing out': this.props.isRemoving,
      'show': !this.props.isRemoving,
      [toastStyle]: true,
    })

    return (
      <div className={className}>
        <a onClick={this.props.remove} className='close-icon'>
          <span className='icon ion-md-close' />
        </a>
        {this.props.children}
      </div>
    )
  }
}

Message.defaultProps = {
  expiry: 5000,
}

Message.propTypes = {
  children: OptionalNode,
  content: OptionalNode,
  expiry: OptionalNumber,
  isRemoving: OptionalBool,
  position: OptionalString,
  remove: RequiredFunc,
}

module.exports = Message

const Toast = class extends React.Component {
  static displayName = 'ToastMessages'

  constructor(props, context) {
    super(props, context)
    this.state = { messages: [], position: 'right' }
    window.toast = this.toast
  }

  toast = (content, expiry, position) => {
    const { messages } = this.state

    const id = Utils.GUID()
    messages.unshift({ content, expiry: E2E ? 1000 : expiry, id })
    this.setState({ messages, position })
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
    const style =
      this.state.position === 'center' ? 'toast-container' : 'toast-messages'
    return (
      <div className={style}>
        {this.state.messages.map((message) => (
          <Message
            key={message.id}
            isRemoving={message.isRemoving}
            remove={() => this.remove(message.id)}
            expiry={message.expiry}
            position={this.state.position}
          >
            {message.content}
          </Message>
        ))}
      </div>
    )
  }
}
module.exports = Toast
