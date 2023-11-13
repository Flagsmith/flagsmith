import React, { Component } from 'react'
import _data from 'common/data/base/_data'

class FlagSelect extends Component {
  state = {
    search: '',
  }

  componentDidMount() {
    this.fetch()
  }

  componentDidUpdate(prevProps) {
    if (prevProps.projectId !== this.props.projectId) {
      this.fetch()
    }
  }

  fetch = () => {
    this.setState({ isLoading: true })
    _data
      .get(
        `${Project.api}projects/${
          this.props.projectId
        }/features/?page=${1}&page_size=${999}&search=${this.state.search}`,
      )
      .then((res) => this.setState({ data: res.results, isLoading: false }))
  }

  // searchFeatures = _.throttle((search) => {
  //     this.fetch()
  // }, 1000)
  //
  // search = (e)=>{
  //     this.setState({search:Utils.safeParseEventValue(e)}, this.searchFeatures)
  // }

  render() {
    if (!this.state.data || this.state.isLoading) {
      return (
        <div className='text-center'>
          <Loader />
        </div>
      )
    }
    const options = _.sortBy(
      this.state.data
        .map((v) => ({ flag: v, label: v.name, value: v.id }))
        .filter((v) => !(this.props.ignore || []).includes(v.value))
        .filter((v) => {
          if (this.props.onlyInclude) {
            if (v.value !== this.props.onlyInclude) {
              return false
            }
          }
          return true
        }),
      (v) => v.label,
    )
    return (
      <Select
        value={
          this.props.value
            ? options.find((v) => v.value === this.props.value)
            : null
        }
        isDisabled={this.props.disabled}
        onInputChange={this.search}
        placeholder={this.props.placeholder}
        onChange={(v) => this.props.onChange(v.value, v.flag)}
        options={options}
      />
    )
  }
}

export default FlagSelect
