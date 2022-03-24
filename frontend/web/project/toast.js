import cn from 'classnames';

const Message = class extends React.Component {
  static displayName = 'Message'

  componentDidMount() {
      setTimeout(this.props.remove, this.props.expiry);
  }

  render() {
      const className = cn({
          'toast-message': true,
          'alert alert-warning fade': true,
          'in': !this.props.isRemoving,
          'removing out': this.props.isRemoving,
      });

      return (
          <div className={className}>
              <a onClick={this.props.remove} className="pull-xs-right">
                  <span className="icon ion-md-close"/>
              </a>
              {this.props.children}
          </div>
      );
  }
};

Message.defaultProps = {
    expiry: 5000,
};

Message.propTypes = {
    children: OptionalNode,
    expiry: OptionalNumber,
    content: OptionalNode,
    remove: RequiredFunc,
    isRemoving: OptionalBool,
};

module.exports = Message;

const Toast = class extends React.Component {
  static displayName = 'ToastMessages'

  constructor(props, context) {
      super(props, context);
      this.state = { messages: [] };
      window.toast = this.toast;
  }

  toast = (content, expiry) => {
      const { messages } = this.state;


      const id = Utils.GUID();
          messages.unshift({ content, expiry: E2E? 1000 : expiry, id });
          this.setState({ messages });
  }

  remove = (id) => {
      const index = _.findIndex(this.state.messages, { id });
      const messages = this.state.messages;

      if (index > -1) {
          messages[index].isRemoving = true;
          setTimeout(() => {
              const index = _.findIndex(this.state.messages, { id });
              const messages = this.state.messages;
              messages.splice(index, 1);
              this.setState({ messages });
          }, 500);
          this.setState({ messages });
      }
  }

  render() {
      return (
          <div className="toast-messages">
              {this.state.messages.map(message => (
                  <Message
                    key={message.id} isRemoving={message.isRemoving}
                    remove={() => this.remove(message.id)}
                    expiry={message.expiry}
                  >
                      {message.content}
                  </Message>
              ))}
          </div>
      );
  }
};
module.exports = Toast;
