import { PureComponent } from 'react';

const Card = class extends PureComponent {
    static displayName = 'Card'

    render() {
        return (
            <div className={`panel-card panel panel-default ${this.props.className || ''}`}>
                <div className="panel-content">
                    {this.props.children}
                </div>
            </div>
        );
    }
};

Card.displayName = 'Card';

Card.propTypes = {
    title: oneOfType([OptionalObject, OptionalString]),
    icon: OptionalString,
    children: OptionalNode,
};

module.exports = Card;
