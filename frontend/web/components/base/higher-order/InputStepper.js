// Attaches an input to a component and exposes current select position with keyboard support
const InputStepper = class extends React.Component {
    static displayName = 'InputStepper'

    blur = () => {
        this.refs.input.blur();
    }

    constructor(props, context) {
        super(props, context);
        this.state = { selectedRow: -1 };
    }

    onFocusChanged = (isFocused) => {
        this.setState({ isFocused, selectedRow: isFocused ? 0 : -1 });
        this.props.onFocusChanged && this.props.onFocusChanged(isFocused);
    }

    onKeyDown = (e) => {
        if (!this.props.data) {
            return;
        }

        if (Utils.keys.isDown(e)) {
            Utils.preventDefault(e);
            this.highlightRow(Math.min(this.state.selectedRow + 1, this.props.data.length - 1));
        } else if (Utils.keys.isUp(e)) {
            Utils.preventDefault(e);
            this.highlightRow(Math.max(this.state.selectedRow - 1, 0));
        } else if (Utils.keys.isEnter(e)) {
            Utils.preventDefault(e);
            this.props.onChange(this.props.data[this.state.selectedRow], e);
        }
    }

    highlightRow = (row) => {
        this.setState({ selectedRow: row });
    }

    render() {
        const theInput = (
            <Input
              ref="input"
              {...this.props.inputProps}
              onBlur={() => this.onFocusChanged(false)}
              onFocus={() => this.onFocusChanged(true)}
              onKeyDown={this.onKeyDown}
            />
        );

        return (
            <div className="list-container">
                {this.props.children(theInput, this.state.selectedRow, this.highlightRow)}
            </div>
        );
    }
};

InputStepper.propTypes = {
    onFocusChanged: OptionalFunc,
    children: RequiredFunc,
    data: OptionalArray,
    onChange: OptionalFunc,
    inputProps: OptionalObject,
};

module.exports = InputStepper;
