import React, { Component } from 'react';
import cx from 'classnames';
import ConfigProvider from '../../../common/providers/ConfigProvider';
import ToggleChip from '../ToggleChip';

const AuditLogPage = class extends Component {
    static displayName = 'AuditLogPage'

    state = {
        search: Utils.fromParam().search,
    };

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    componentDidMount() {
        const { env } = this.getEnvironment();
        AppActions.getAuditLog(this.props.match.params.projectId, this.state.search, env);
        API.trackPage(Constants.pages.AUDIT_LOG);
    }

    filterRow = (logMessage, search) => {
        const stringToSearch = `${logMessage.log} ${logMessage.author ? logMessage.author.first_name : ''} ${logMessage.author ? logMessage.author.last_name : ''} ${logMessage.author ? logMessage.author.email : ''} ${moment(logMessage.created_date).format('L LTS')}`;
        return stringToSearch.toLowerCase().indexOf(search.toLowerCase()) !== -1;
    }

    renderRow = ({ created_date, log, author }) => (
        <Row space className="list-item audit__item" key={created_date}>
            <Flex>
                <div
                  className="audit__log"
                >
                    {log}
                </div>
                <div
                  className="audit__author"
                >
                    {author ? `${author.first_name} ${author.last_name}` : 'Unknown'}
                </div>
            </Flex>
            <div className="audit__date">{moment(created_date).format('Do MMM YYYY HH:mma')}</div>
        </Row>
    )

    toggleEnv = (env) => {
        const filters = Utils.fromParam();
        if (filters.env && filters.env === `${env.id}`) {
            delete filters.env;
        } else {
            filters.env = `${env.id}`;
        }
        AppActions.getAuditLog(this.props.match.params.projectId, this.state.search, env.id);
        this.context.router.history.replace(`${document.location.pathname}?${Utils.toParam(filters)}`);
    }

    filterSearch =(e) => {
        this.setState({ search: Utils.safeParseEventValue(e) });
    }

    saveSearch =(e) => {
        const filters = Utils.fromParam();
        filters.search = this.state.search;
        if (!filters.search) {
            delete filters.search;
        }
        this.context.router.history.replace(`${document.location.pathname}?${Utils.toParam(filters)}`);
    }


    getEnvironment = () => {
        const { env } = Utils.fromParam();
        return { env };
    }

    render() {
        const { state: { search } } = this;
        const { env: envFilter } = this.getEnvironment();
        const hasRbacPermission = !Utils.getFlagsmithHasFeature('plan_based_access') || Utils.getPlansPermission('AUDIT') || !this.props.hasFeature('scaleup_audit');
        if (!hasRbacPermission) {
            return (
                <div>
                    <div className="text-center">
                      To access this feature please upgrade your account to scaleup or higher.
                    </div>
                </div>
            );
        }
        return (
            <div className="app-container container">

                <div>
                    <div>
                        <h3>Audit Log</h3>
                        <p>
                            View all activity that occured generically across the project and specific to this environment.
                        </p>
                        <FormGroup>
                            <AuditLogProvider>
                                {({ isLoading, auditLog: _auditLog, auditLogPaging: _auditLogPaging }) => {
                                    const { env } = Utils.fromParam();
                                    const auditLog = _auditLog && _auditLog[env || this.props.match.params.projectId];
                                    const auditLogPaging = _auditLogPaging && _auditLogPaging[env || this.props.match.params.projectId];
                                    return (
                                        <div>
                                            <div className="audit">
                                                <div className="font-weight-bold mb-2">
                                                    Filter by environments:
                                                </div>
                                                <ProjectProvider>
                                                    {({ project }) => (
                                                        <Row>
                                                            {project && project.environments && project.environments.map(env => (
                                                                <ToggleChip active={envFilter === `${env.id}`} onClick={() => this.toggleEnv(env)} className="mr-2 mb-4">
                                                                    {env.name}
                                                                </ToggleChip>
                                                            ))}
                                                        </Row>
                                                    )}
                                                </ProjectProvider>
                                                <FormGroup>
                                                    <PanelSearch
                                                      onBlur={this.saveSearch}
                                                      id="messages-list"
                                                      title="Log entries"
                                                      isLoading={isLoading || (!auditLog)}
                                                      className="no-pad"
                                                      icon="ion-md-browsers"
                                                      items={auditLog}
                                                      search={search}
                                                      filter={envFilter}
                                                      onChange={(e) => {
                                                          this.setState({ search: Utils.safeParseEventValue(e) });
                                                          AppActions.searchAuditLog(Utils.safeParseEventValue(e), this.props.match.params.projectId, env);
                                                      }}
                                                      paging={auditLogPaging}
                                                      nextPage={() => AppActions.getAuditLogPage(this.props.match.params.projectId, auditLogPaging.next, env)}
                                                      prevPage={() => AppActions.getAuditLogPage(this.props.match.params.projectId, auditLogPaging.previous, env)}
                                                      goToPage={page => AppActions.getAuditLogPage(this.props.match.params.projectId, `${Project.api}audit/?page=${page}`, env)}
                                                      renderRow={this.renderRow}
                                                      renderNoResults={(
                                                          <FormGroup className="text-center">
                                                                You have no
                                                                log messages
                                                                for your
                                                                project.
                                                          </FormGroup>
                                                        )}
                                                      filterRow={this.filterRow}
                                                    />
                                                </FormGroup>
                                            </div>
                                        </div>
                                    );
                                }}
                            </AuditLogProvider>
                        </FormGroup>
                    </div>
                </div>
            </div>
        );
    }
};

AuditLogPage.propTypes = {};

module.exports = ConfigProvider(AuditLogPage);
