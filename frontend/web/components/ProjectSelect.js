import React, { Component } from 'react';

const ProjectSelect = class extends Component {
    static displayName = 'ProjectSelect'

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    render() {
        return (
            <OrganisationProvider id={this.props.id}>
                {({ isLoading, projects }) => (
                    <>
                        {
                            <div className={`fade ${projects && !!projects.length && 'in'}`}>
                                {projects && !!projects.length
                                    && projects.map(project => this.props.renderRow(project,
                                        () => {
                                            this.props.onChange && this.props.onChange(project);
                                        }))
                                }
                            </div>
                        }
                    </>
                )}
            </OrganisationProvider>
        );
    }
};

ProjectSelect.propTypes = {};

module.exports = ConfigProvider(ProjectSelect);
