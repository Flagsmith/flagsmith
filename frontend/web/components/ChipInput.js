// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import TheInput from 'material-ui-chip-input';

export default class ChipInput extends PureComponent {
  static displayName = 'ChipInput';

  static propTypes = {};

  constructor(props) {
      super(props);
      this.state = {
          chips: [],
      };
  }

  onChange = (chips) => {
      this.setState({ chips, inputValue: '' });
      this.props.onChange(chips);
  }

  onChangeText = (e) => {
      const v = Utils.safeParseEventValue(e);
      const currentValue = this.state.chips || [];
      if (v.search(/[ ,]/) !== -1) {
          const split = _.filter(v.split(/[ ,;]/), v => v !== ' ' && v !== ',' && v !== ';' && v !== '');
          this.onChange(currentValue.concat(split));
      } else {
          this.setState({ inputValue: v });
      }
  }

  onDelete = (chip, index) => {
      this.state.chips.splice(index, 1);
      this.onChange(this.state.chips);
  }

  onSubmit = (chip, index) => {
      if (chip) {
          this.state.chips.push(chip);
          this.onChange(this.state.chips);
      }
  }

  render() {
      return (
          <TheInput
            color="red"
            fullWidth
            placeholder={this.props.placeholder}
            blurBehavior="add"
            onChangeCapture={this.onChangeText}
            value={this.state.chips}
            inputValue={this.state.inputValue}
            onDelete={this.onDelete}
            onBeforeAdd={this.onSubmit}
            onChange={this.onChange}
          />
      );
  }
}
