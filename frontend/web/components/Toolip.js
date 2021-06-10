const ReactTooltip = require('react-tooltip');

const Tooltip = class extends React.Component {
  static displayName = 'Tooltip';

  id = Utils.GUID();

  render() {
      return (
          <span className="question-tooltip">
              {this.props.title ? <span data-for={this.id} data-tip>{this.props.title}</span>
                  : <span className="ion ion-ios-help" data-for={this.id} data-tip/>}
              <ReactTooltip
                html
                id={this.id} place={this.props.place || 'top'} type="dark"
                effect="solid"
              >
                  {
                  `<div class="flex-row"><div class="icon--tooltip ion-ios-information-circle pr-2"></div><span>${this.props.children}</span></div>`
                }
              </ReactTooltip>
          </span>
      );
  }
};

Tooltip.propTypes = {
    children: RequiredElement,
    place: OptionalString,
};

module.exports = Tooltip;
