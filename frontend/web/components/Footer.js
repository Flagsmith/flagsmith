const data = require('../../common/data/base/_data');

const Footer = class extends React.Component {
  state = {
      operational: true,
  }

  componentDidMount() {
  }

  render() {
      const { hasFeature, className } = this.props;
      return (
          <footer className={`${className} clearfix`}>
              <div className="container">
                  <div className="row footer__homepage-content pt-5">
                      <div className="col-md-4">
                          <img src="/images/nav-logo.svg" width={166} alt="Flagsmith Logo"
className="img-responsive"/>
                          <div className="service-status">
                              <a href="https://status.bullet-train.io/">
                                  {this.state.operational
                                      ? (
                                          <div>
                                              <span className="dot green" />
                                              Flagsmith services are operational
                                          </div>
                                      )
                                      : (
                                          <div>
                                              <span className="dot orange" />
                                              Flagsmith services are experiencing problems. Click
                                              {' '}
                                              <a href="https://cachet.dokku1.solidstategroup.com/">here</a>
                                              {' '}
                                              for more info
                                          </div>
                                      )
                                  }
                              </a>
                          </div>

                          <ul className="list-inline">
                              <li className="list-inline-item">
                                  <a href="https://github.com/Flagsmith" title="GitHub">
                                      <span className="icon ion-logo-github"/>
                                  </a>
                              </li>
                              <li className="list-inline-item">
                                  <a href="https://twitter.com/GetBulletTrain" title="Twitter">
                                      <span className="pl-4 icon ion-logo-twitter"/>
                                  </a>
                              </li>
                          </ul>
                      </div>
                      <div className="col-md-2 offset-md-2">
                          <h6>Product</h6>
                          <ul className=" float-left nav-list">
                              <li><Link to="/demo">Demo</Link></li>
                              <li><a href="https://docs.flagsmith.com/">Docs</a></li>
                              <li><Link to="/pricing#pricing">Pricing</Link></li>
                          </ul>
                      </div>
                      <div className="col-md-2">
                          <h6>Support</h6>
                          <ul className=" float-left nav-list">
                              <li><a href="mailto:support@bullet-train.io">Contact Us</a></li>
                              <li><a href="https://status.bullet-train.io/">Status</a></li>
                              <li><Link to="/blog/remote-config-and-feature-flags">What are feature flags?</Link></li>
                              <li><Link to="/blog/remote-config-and-feature-flags">What is remote config?</Link></li>
                          </ul>
                      </div>
                      <div className="col-md-2">
                          <h6>Company</h6>
                          <ul className=" float-left nav-list">
                              <li><Link to="/legal/tos">Terms of Service</Link></li>
                              <li><Link to="/legal/privacy-policy">Privacy Policy</Link></li>
                              <li><Link to="/legal/sla">Service Level Agreement</Link></li>
                          </ul>
                      </div>
                  </div>
              </div>

          </footer>
      );
  }
};

export default ConfigProvider(Footer);
