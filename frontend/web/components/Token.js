import React, { Component } from 'react'

class Token extends Component {
  constructor(props) {
    super()
    this.state = {
      showToken: !!props.show,
    }
  }

  render() {
    if (!this.props.token) return null
    return (
      <Row>
        <Input
          inputProps={{
            readOnly: true,
          }}
          value={
            this.state.showToken
              ? this.props.token
              : this.props.token
                  .split('')
                  .map(() => '*')
                  .join('')
                  .trim()
          }
          style={this.props.style}
          className={`${this.state.showToken ? 'font-weight-bold' : ''}`}
        />
        {this.props.show ? (
          <Button
            theme='outline'
            style={{ width: 80 }}
            className='btn-secondary ml-2 mr-4'
            onClick={() => {
              navigator.clipboard.writeText(this.props.token)
              toast('Copied')
            }}
          >
            Copy
          </Button>
        ) : (
          <Button
            style={{ width: 80 }}
            className='ml-2 mr-4'
            onClick={() => this.setState({ showToken: !this.state.showToken })}
          >
            {this.state.showToken ? 'Hide' : 'Show'}
          </Button>
        )}
      </Row>
    )
  }
}

export default Token
