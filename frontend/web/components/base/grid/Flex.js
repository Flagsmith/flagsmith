const Flex = class extends React.Component {
  static displayName = 'Flex'

  render() {
    return (
      <div
        {...this.props}
        className={`${this.props.className || ''} flex flex-1`}
      >
        {this.props.children}
      </div>
    )
  }
}

Flex.defaultProps = {
  value: 1,
}

Flex.propTypes = {
  children: OptionalNode,
  className: OptionalString,
  style: propTypes.any,
  value: OptionalNumber,
}

module.exports = Flex
