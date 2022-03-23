import { render } from 'react-dom';
import React from 'react';

const Provider = class extends React.Component {
    componentDidMount() {
        if (this.props.type !== 'confirm') {
            if (this.props.isModal2) {
                window.closeModal2 = this.close;
            } else {
                window.closeModal = this.close;
            }
        }
        $(ReactDOM.findDOMNode(this)).on('hidden.bs.modal', this._closed);
        $(ReactDOM.findDOMNode(this)).on('shown.bs.modal', this._shown);
        $(ReactDOM.findDOMNode(this)).modal({ background: true, keyboard: true, show: true });
    }

    show() {
        $(ReactDOM.findDOMNode(this)).on('hidden.bs.modal', this.unmount);
        $(ReactDOM.findDOMNode(this)).modal('show');
        $(ReactDOM.findDOMNode(this)).style = '';
    }

  close = () => { // use when you wish to trigger closing manually
      $(ReactDOM.findDOMNode(this)).off('hidden.bs.modal', this._closed);
      $(ReactDOM.findDOMNode(this)).off('shown.bs.modal', this._shown);
      if (!E2E) {
          $(ReactDOM.findDOMNode(this)).modal('hide');
          setTimeout(() => {
              ReactDOM.unmountComponentAtNode(document.getElementById(this.props.type == 'confirm' ? 'confirm' : this.props.isModal2 ? 'modal2' : 'modal'));
              document.body.classList.remove('modal-open');
          }, E2E ? 0 : 500);
      } else {
          // for e2e we disable any animations and immediately remove from the DOM
          $('.modal-backdrop').remove();
          ReactDOM.unmountComponentAtNode(document.getElementById(this.props.type == 'confirm' ? 'confirm' : this.props.isModal2 ? 'modal2' : 'modal'));
          document.body.classList.remove('modal-open');
      }
  }

  _closed = () => {
      this.props.onClose && this.props.onClose();
      ReactDOM.unmountComponentAtNode(document.getElementById(this.props.type == 'confirm' ? 'confirm' : this.props.isModal2 ? 'modal2' : 'modal'));
      document.body.classList.remove('modal-open');
  }

  _shown() {
      this.isVisible = true;
  }

  render() {
      return this.props.children;
  }
};

Provider.propTypes = {
    children: RequiredElement,
    onClose: OptionalFunc,
};

const Modal = class extends React.Component {
    header() {
        return this.props.header || '';
    }

    body() {
        return this.props.body || '';
    }

    footer() {
        return this.props.footer || '';
    }

  close = () => {
      if (this.props.isModal2) {
          closeModal2();
      } else {
          closeModal();
      }
  }

  render() {
      return (
          <Provider isModal2={this.props.isModal2} ref="modal">
              <div
                tabIndex="-1" className={`modal ${E2E ? 'transition-none ' : ''}${this.props.className ? this.props.className : 'alert fade expand'}`} role="dialog"
                aria-hidden="true"
              >
                  <div className={`modal-dialog ${this.props.large ? 'modal-lg' : ''}`}>
                      <div className="modal-content">
                          <div className="modal-header">
                              {this.header()}
                              {isMobile && (
                              <button onClick={() => this.refs.modal.close()} className="modal-close-btn">
                                  <span className="icon ion-md-close"/>
                              </button>
                              )}
                              <span onClick={this.close} className="icon close ion-md-close"/>
                          </div>
                          <div className="modal-body">{this.body()}</div>
                          <div className="modal-footer">{this.footer()}</div>
                      </div>
                  </div>
              </div>
          </Provider>
      );
  }
};

Modal.propTypes = {
    header: OptionalNode,
    body: OptionalNode,
    footer: OptionalNode,
};

const Confirm = class extends React.Component {
    header() {
        return this.props.header || '';
    }

    body() {
        return this.props.body || '';
    }

  onNo = () => {
      this.props.onNo && this.props.onNo();
      this.refs.modal.close();
  }

  onYes = () => {
      this.props.onYes && this.props.onYes();
      this.refs.modal.close();
  }

  closed() {
      this.onNo();
  }

  footer() {
      return (
          <div className="modal-button">
              <Row style={{ justifyContent: 'flex-end' }}>
                  <Column>
                      <a
                        href="#"
                        className="btn-link btn-link-secondary"
                        id="confirm-btn-no"
                        onClick={this.onNo}
                      >
                          {this.props.noText || 'No'}
                      </a>
                  </Column>
                  <Column>
                      <a
                        href="#"
                        className="btn-link btn-link-secondary"
                        id="confirm-btn-yes"
                        onClick={this.onYes}
                      >
                          {this.props.yesText || 'Yes'}
                      </a>
                  </Column>
              </Row>
          </div>
      );
  }

  render() {
      return (
          <Provider onClose={this.props.onNo} ref="modal" type="confirm">
              <div
                tabIndex="-1" className="modal alert modal-confirm fade expand" role="dialog"
                aria-hidden="true"
              >
                  <div className="modal-dialog">
                      <div className="modal-content">
                          <div className="modal-header">{this.header()}</div>
                          <div className="modal-body">{this.body()}</div>
                          <div className="modal-footer">{this.footer()}</div>
                      </div>
                  </div>
              </div>
          </Provider>
      );
  }
};

Confirm.propTypes = {
    header: OptionalNode,
    body: OptionalNode,
    onYes: OptionalFunc,
    onNo: OptionalFunc,
    yesText: OptionalString,
    noText: OptionalString,
};

exports.openModal = (header, body, footer, other) => {
    render(<Modal
      header={header} footer={footer} body={body}
      {...other}
    />, document.getElementById('modal'));
};

exports.openModal2 = (header, body, footer, other) => {
    render(<Modal
      isModal2
      header={header} footer={footer} body={body}
      {...other}
    />, document.getElementById('modal2'));
};

exports.openConfirm = (header, body, onYes, onNo) => {
    render(<Confirm
      header={header} onYes={onYes} onNo={onNo}
      body={body}
    />, document.getElementById('confirm'));
};
