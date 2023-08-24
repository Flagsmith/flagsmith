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
          value={this.props.token}
          style={this.props.style}
          className={`${
            this.state.showToken ? 'font-weight-bold' : ''
          } full-width`}
          type='password'
        />
        {this.props.show && (
          <Button
            theme='outline'
            style={{ width: 80 }}
            className='ml-2 mr-4'
            onClick={() => {
              navigator.clipboard.writeText(this.props.token)
              toast('Copied')
            }}
          >
            Copy
          </Button>
        )}
      </Row>
    )
  }
}

export default Token
