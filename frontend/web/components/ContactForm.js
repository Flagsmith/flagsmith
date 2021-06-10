import data from '../../common/data/base/_data'
export class ContactForm extends React.Component {
  static displayName = 'TheComponent';

  static propTypes = {};

  state = {

  }

  submit = (e) => {
      Utils.preventDefault(e);
      this.setState({ isLoading: true });
      const { isLoading, ...rest } = this.state;
      data.post('https://post.formlyapp.com/bullet-train-a6b7d1', { ...rest })
          .then(() => {
              this.setState({ isComplete: true });
              this.props.onComplete();
          }).catch(() => {
              this.setState({ isLoading: false });
          });
  }

  render() {
      // const { props } = this;
      return this.state.isComplete ? (
          <div>
        Thank you for contacting us, a member of our sales team will get in touch within 24 hours.
          </div>
      ) : (
          <form onSubmit={this.submit}>
              <InputGroup
                title="Email Address*"
                inputProps={{
                    className: 'full-width modal-input mb-2',
                }}
                onChange={e => this.setState({ email: Utils.safeParseEventValue(e) })}
              />
              <InputGroup
                title="Expected requests per month (optional)"
                inputProps={{
                    className: 'full-width modal-input mb-2',
                }}
                onChange={e => this.setState({ callsPerMonth: Utils.safeParseEventValue(e) })}
              />
              <InputGroup
                title="Number of team members (optional)"
                inputProps={{
                    className: 'full-width modal-input mb-2',
                }}
                onChange={e => this.setState({ numberOfSeats: Utils.safeParseEventValue(e) })}
              />
              <InputGroup
                title="How can we help?"
                textarea
                inputProps={{
                    style: { height: 100 },
                    className: 'full-width modal-input mb-2',
                }}
                onChange={e => this.setState({ message: Utils.safeParseEventValue(e) })}
              />
              <div className="text-right">
                  <Button type="submit" style={{ paddingLeft: 50, paddingRight: 50, fontSize: 18 }} disabled={this.state.isLoading || !Utils.isValidEmail(this.state.email)}>
            Contact Sales
                  </Button>
              </div>

          </form>
      );
  }
}
