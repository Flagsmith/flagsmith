import React, { Component } from 'react';
import Tabs from './base/forms/Tabs';
import TabItem from './base/forms/TabItem';
import Highlight from './Highlight';

const getGithubLink = (key) => {
    switch (key) {
        case '.NET':
            return 'https://github.com/flagsmith/flagsmith-dotnet-client/';
        case 'Flutter':
            return 'https://github.com/flagsmith/flagsmith-flutter-client/';
        case 'Go':
            return 'https://github.com/flagsmith/flagsmith-go-client/';
        case 'Java':
            return 'https://github.com/flagsmith/flagsmith-java-client/';
        case 'JavaScript':
            return 'https://github.com/flagsmith/flagsmith-js-client/';
        case 'Node JS':
            return 'https://github.com/flagsmith/flagsmith-nodejs-client/';
        case 'PHP':
            return 'https://github.com/flagsmith/flagsmith-php-client/';
        case 'Python':
            return 'https://github.com/flagsmith/flagsmith-python-client/';
        case 'REST':
            return 'https://docs.flagsmith.com/clients/rest/';
        case 'React Native':
            return 'https://github.com/flagsmith/flagsmith-js-client/';
        case 'Ruby':
            return 'https://github.com/flagsmith/flagsmith-ruby-client/';
        case 'Rust':
            return 'https://github.com/flagsmith/flagsmith-rust-client/';
        case 'iOS':
            return 'https://github.com/flagsmith/flagsmith-ios-client/';
        default:
            return 'https://docs.flagsmith.com';
    }
};
const getDocsLink = (key) => {
    switch (key) {
        case '.NET':
            return 'https://docs.flagsmith.com/clients/dotnet/';
        case 'Flutter':
            return 'https://docs.flagsmith.com/clients/flutter/';
        case 'Go':
            return 'https://docs.flagsmith.com/clients/go/';
        case 'Java':
            return 'https://docs.flagsmith.com/clients/java/';
        case 'JavaScript':
            return 'https://docs.flagsmith.com/clients/javascript/';
        case 'Node JS':
            return 'https://docs.flagsmith.com/clients/node/';
        case 'PHP':
            return 'https://docs.flagsmith.com/clients/php/';
        case 'Python':
            return 'https://docs.flagsmith.com/clients/python/';
        case 'REST':
            return null;
        case 'React':
            return 'https://docs.flagsmith.com/clients/react';
        case 'React Native':
            return 'https://docs.flagsmith.com/clients/react';
        case 'Ruby':
            return 'https://docs.flagsmith.com/clients/ruby/';
        case 'Rust':
            return 'https://docs.flagsmith.com/clients/rust/';
        case 'iOS':
            return 'https://docs.flagsmith.com/clients/ios/';
        case 'Next.js':
            return 'https://docs.flagsmith.com/clients/next-ssr';
        default:
            return 'https://docs.flagsmith.com';
    }
};

const CodeHelp = class extends Component {
    static displayName = 'CodeHelp'

    constructor(props, context) {
        super(props, context);
        this.state = {
            visible: this.props.showInitially || this.props.hideHeader,
        };
    }


    copy = (s) => {
        const res = Clipboard.setString(s);
        toast(res ? 'Clipboard set' : 'Could not set clipboard :(');
    };

    render() {
        const { hideHeader } = this.props;
        const language = this.state.language || flagsmith.getTrait('preferred_language') || Object.keys(this.props.snippets)[0];
        const tab = language ? Math.max(Object.keys(this.props.snippets).indexOf(language), 0) : 0;
        return (
            <div>
                {!hideHeader && (
                    <div
                      style={{ cursor: 'pointer' }} onClick={() => {
                          this.setState({ visible: !this.state.visible });
                      }}
                    >
                        <Row>
                            <Flex style={isMobile ? { overflowX: 'scroll' } : {}}>
                                <div>
                                    <pre className="hljs-header">
                                        <span className="ion-ios-code"/>
                                        {' '}
Code example:
                                        {' '}
                                        <span className="hljs-description">
                                            {this.props.title}
                                            {' '}
                                        </span>
                                        <span
                                          className={this.state.visible ? 'icon ion-ios-arrow-down' : 'icon ion-ios-arrow-forward'}
                                        />
                                    </pre>
                                </div>
                            </Flex>
                        </Row>
                    </div>
                )}

                {this.state.visible && (
                    <>
                            {this.props.subtitle && (
                                <div className="mb-2">
                                    {this.props.subtitle}
                                </div>
                            )}

                        <div className="code-help">
                            <Select
                              data-test="select-segment"
                              placeholder="Select a language"
                              value={{
                                  label: language,
                              }}
                              onChange={(v) => {
                                  const lang = v.label;
                                  this.setState({ language: lang });
                                  flagsmith.setTrait('preferred_language', lang);
                                  this.setState({ tab });
                              }}
                              options={
                                    Object.keys(this.props.snippets).map((v, i) => (
                                        {
                                            label: v,
                                            value: i,
                                        }
                                    ))
                                }
                              styles={{
                                  control: base => ({
                                      ...base,
                                      width: 200,
                                      alignSelf: 'flex-end',
                                      '&:hover': { borderColor: '$bt-brand-secondary' },
                                      border: '1px solid $bt-brand-secondary',
                                  }),
                              }}
                            />
                            <Tabs
                              value={tab}
                              onChange={(tab) => {
                                  const lang = Object.keys(this.props.snippets)[tab];
                              }}
                            >
                                {_.map(this.props.snippets, (s, key) => {
                                    const docs = getDocsLink(key);
                                    const github = getGithubLink(key);
                                    return (
                                        <TabItem key={key} tabLabel={key}>
                                            <div className="hljs-container mb-2">
                                                <Highlight preventEscape className={Constants.codeHelp.keys[key]}>
                                                    {s}
                                                </Highlight>
                                                <Button onClick={() => this.copy(s)} className="btn btn-primary hljs-copy">
                                                    Copy Code
                                                </Button>
                                                <Row className="hljs-docs">
                                                    {docs && (
                                                        <a
                                                          target="_blank" href={docs}
                                                          className="btn btn--docs"
                                                        >
                                                            <ion className="icon ion ion-ios-document"/>

                                                            {' '}{key} Docs
                                                        </a>
                                                    )}
                                                    {github && (
                                                        <a
                                                          target="_blank" href={github}
                                                          className="btn btn--docs"
                                                        >
                                                            <ion className="icon ion ion-logo-github"/>
                                                            {' '}{key} GitHub
                                                        </a>
                                                    )}
                                                </Row>


                                            </div>
                                        </TabItem>
                                    );
                                })}
                            </Tabs>
                        </div>
                    </>

                )}

            </div>
        );
    }
};

CodeHelp.propTypes = {};

module.exports = ConfigProvider(CodeHelp);
