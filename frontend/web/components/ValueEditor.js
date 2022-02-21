import React from 'react';
import { Component } from 'react';
import cx from 'classnames';
import Highlight from './Highlight';
import ConfigProvider from '../../common/providers/ConfigProvider';

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

    render() {
        const { ...rest } = this.props;
        return (
            <div className={cx('value-editor', { light: this.state.language === 'txt' })}>
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
                    .json
                    </span>
                    <span
                      onMouseDown={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          this.setState({ language: 'xml' });
                      }}
                      className={cx('xml', { active: this.state.language === 'xml' })}
                    >
                    .xml
                    </span>
                    <span
                      onMouseDown={(e) => {
                          e.preventDefault();
                          e.stopPropagation();

                          this.setState({ language: 'ini' });
                      }}
                      className={cx('ini', { active: this.state.language === 'ini' })}
                    >
                    .toml
                    </span>
                    <span
                      onMouseDown={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          this.setState({ language: 'yaml' });
                      }}
                      className={cx('yaml', { active: this.state.language === 'yaml' })}
                    >
                    .yaml
                    </span>
                    <span
                        onMouseDown={(e) => {
                            const res = Clipboard.setString(this.props.value);
                            toast(res ? 'Clipboard set' : 'Could not set clipboard :(');
                        }}
                        className={cx('txt primary' )}
                    >
                        <span className="ion ion-md-clipboard mr-0 ml-2 txt primary"/> copy

                    </span>
                </Row>
                {this.state.language === 'txt' ? (
                    <textarea
                      {...rest}
                    />
                ) : (
                    <Highlight data-test={rest['data-test']} onChange={rest.onChange} className={this.state.language}>
                        {rest.value}
                    </Highlight>
                )}


            </div>
        );
    }
}

export default ConfigProvider(ValueEditor);
