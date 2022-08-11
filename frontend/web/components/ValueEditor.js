import React from 'react';
import { Component } from 'react';
import cx from 'classnames';
import Highlight from './Highlight';
import ConfigProvider from '../../common/providers/ConfigProvider';


const toml = require('toml');
const yaml = require('yaml');

function xmlIsInvalid(xmlStr) {
    const parser = new DOMParser();
    const dom = parser.parseFromString(xmlStr, 'application/xml');
    for (const element of Array.from(dom.querySelectorAll('parsererror'))) {
        if (element instanceof HTMLElement) {
            // Found the error.
            return element.innerText;
        }
    }
    // No errors found.
    return false;
}

class Validation extends Component {
    constructor(props) {
        super(props);
        this.state = {};
        this.validateLanguage(this.props.language, this.props.value);
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (prevProps.value !== this.props.value || prevProps.language !== this.props.language) {
            this.validateLanguage(this.props.language, this.props.value);
        }
    }

    validateLanguage = (language, value) => {
        const validate = new Promise((resolve) => {
            switch (language) {
                case 'json': {
                    try {
                        JSON.parse(value);
                        resolve(false);
                    } catch (e) {
                        resolve(e.message);
                    }
                    break;
                }
                case 'ini': {
                    try {
                        toml.parse(value);
                        resolve(false);
                    } catch (e) {
                        resolve(e.message);
                    }
                    break;
                }
                case 'yaml': {
                    try {
                        yaml.parse(value);
                        resolve(false);
                    } catch (e) {
                        resolve(e.message);
                    }
                    break;
                }
                case 'xml': {
                    try {
                        const error = xmlIsInvalid(value);
                        resolve(error);
                    } catch (e) {
                        resolve('Failed to parse XML');
                    }
                    break;
                }
            }
        });

        validate.then((error) => {
            this.setState({ error });
        });
    }

    render() {
        const displayLanguage = this.props.language === 'ini' ? 'toml' : this.props.language;
        return (
            <Tooltip position="top" title={!this.state.error ? <ion className="text-white ion-ios-checkmark-circle"/> : <ion id="language-validation-error" className="text-white ion-ios-warning"/>}>
                {!this.state.error ? `${displayLanguage} validation passed` : `${displayLanguage} validation error, please check your value.<br/>Error: ${this.state.error}`}
            </Tooltip>
        );
    }
}
class ValueEditor extends Component {
    state = {
        language: 'txt',
    };

    componentDidMount() {
        if (!this.props.value) return;
        try {
            const v = JSON.parse(this.props.value);
            if (typeof v !== 'object') return;
            this.setState({ language: 'json' });
        } catch (e) {
        }
        // document.querySelector('[contenteditable]').addEventListener('paste', function (event) {
        //     event.preventDefault();
        //     document.execCommand('inserttext', false, event.clipboardData.getData('text/plain'));
        // });
    }

    renderValidation = () => <Validation language={this.state.language} value={this.props.value}/>

    render() {
        const { ...rest } = this.props;
        return (
            <div className={cx('value-editor')}>
                <Row className="select-language">
                    <span
                      onMouseDown={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          this.setState({ language: 'txt' });
                      }}
                      className={cx('txt', { active: this.state.language === 'txt' })}
                    >
                    .txt
                    </span>
                    <span
                      onMouseDown={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          this.setState({ language: 'json' });
                      }}
                      className={cx('json', { active: this.state.language === 'json' })}
                    >
                    .json {this.state.language === 'json' && this.renderValidation()}
                    </span>
                    <span
                      onMouseDown={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          this.setState({ language: 'xml' });
                      }}
                      className={cx('xml', { active: this.state.language === 'xml' })}
                    >
                    .xml {this.state.language === 'xml' && this.renderValidation()}
                    </span>
                    <span
                      onMouseDown={(e) => {
                          e.preventDefault();
                          e.stopPropagation();

                          this.setState({ language: 'ini' });
                      }}
                      className={cx('ini', { active: this.state.language === 'ini' })}
                    >
                        .toml {this.state.language === 'ini' && this.renderValidation()}
                    </span>
                    <span
                      onMouseDown={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          this.setState({ language: 'yaml' });
                      }}
                      className={cx('yaml', { active: this.state.language === 'yaml' })}
                    >
                        .yaml {this.state.language === 'yaml' && this.renderValidation()}
                    </span>
                    <span
                      onMouseDown={(e) => {
                          const res = Clipboard.setString(this.props.value);
                          toast(res ? 'Clipboard set' : 'Could not set clipboard :(');
                      }}
                      className={cx('txt primary')}
                    >
                        <span className="ion ion-md-clipboard mr-0 ml-2 txt primary"/> copy

                    </span>
                </Row>

                <Highlight data-test={rest['data-test']} onChange={rest.onChange} className={this.state.language}>
                    {rest.value}
                </Highlight>


            </div>
        );
    }
}

export default ConfigProvider(ValueEditor);
