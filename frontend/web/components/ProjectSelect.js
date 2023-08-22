import React, { Component } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'

const ProjectSelect = class extends Component {
  static displayName = 'ProjectSelect'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = { search: '' }
  }

  render() {
    return (
      <OrganisationProvider id={this.props.id}>
        {({ projects }) => (
          <>
            {
              <div className='project-select ml-5 mr-3 mb-2 pb-2'>
                <div className='project-select-header mb-2'>
                  <Input
                    search
                    size='xSmall'
                    className='full-width'
                    onChange={(e) => {
                      this.setState({
                        search: Utils.safeParseEventValue(e),
                      })
                    }}
                    value={this.state.search}
                    autoFocus
                  />
                </div>
                <div className='project-select-body'>
                  {projects &&
                  projects.filter((el) =>
                    el.name
                      .toLowerCase()
                      .includes(this.state.search.toLowerCase()),
                  ).length ? (
                    projects.map((project) => {
                      if (
                        project.name
                          .toLowerCase()
                          .includes(this.state.search.toLowerCase())
                      ) {
                        return this.props.renderRow(project, () => {
                          this.props.onChange && this.props.onChange(project)
                        })
                      }
                    })
                  ) : (
                    <div className='mx-3 mt-2 text-white'>No results</div>
                  )}
                </div>
              </div>
            }
          </>
        )}
      </OrganisationProvider>
    )
  }
}

ProjectSelect.propTypes = {}

module.exports = ConfigProvider(ProjectSelect)
