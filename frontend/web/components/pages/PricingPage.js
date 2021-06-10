import React from 'react';
import Footer from '../Footer';
import PricingPanel from '../PricingPanel';
import Feedback from '../modals/Feedback';

const PricingPage = class extends React.Component {
    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    static displayName = 'PricingPage'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    componentDidMount() {
        API.trackPage(Constants.pages.PRICING);
    }

    feedback = () => {
        openModal('Feedback', <Feedback/>);
    }

    render = () => {
        const { hasFeature, getValue } = this.props;
        const redirect = Utils.fromParam().redirect ? `?redirect=${Utils.fromParam().redirect}` : '';

        return (
            <div data-test="pricing-page">
                <PricingPanel redirect={redirect}/>

                <div className="faq">
                    <div className="container">
                        <h2 className="text-center margin-bottom">FAQs</h2>
                        <div className="panel panel-default panel-grey">
                            <p className="question">So how does this all work?</p>
                            <p className="answer">
                                First off, you're free to host Flagsmith yourself, free of charge. We're open source,
                                and totally fine with you doing that.
                            </p>
                            <p className="answer">
                                If you want to support the project, or you don't fancy going through the hassle of
                                managing that infrastructure, we'd love you to sign up.
                            </p>
                            <p className="answer">
                                The only metric you need to count when deciding on your plan is the number of Monthly
                                Active Users you need to serve flags for (see below).
                                You can create as many projects, flags, admin users as you like. We feel that this is
                                the fairest measure of usage.
                            </p>
                        </div>
                        <div className="panel panel-default panel-grey">
                            <p className="question">How do you calculate requests per month</p>
                            <p className="answer">
                                This is simply the total number of API requests you make for each calendar month, across
                                all the projects in your organisation.
                            </p>
                            <p className="answer">
                                Each time you instantiate one of our client SDKs and get the flags for a user or
                                application, you make 1 request.
                                For example, if you have a single page React web application, you would generally make 1
                                API request when the user loads your app, and then
                                maintain that data for the duration of the user session. If your web pages were
                                generated server-side, you would generally make 1 API request
                                for each page view.
                            </p>
                        </div>
                        <div className="panel panel-default panel-grey">
                            <p className="question">What is a Team Member?</p>
                            <p className="answer">
                                Each Team Member can log in with their own email address. Audit logs record activities per
                                logged in Team Member.
                            </p>
                        </div>
                        <div className="panel panel-default panel-grey">
                            <p className="question">What happens if I go over my plan limit?</p>
                            <p className="answer">
                                Don't worry - we'll carry on serving your flags to your users. We realise that this is
                                important to your application.
                                If this does happen, we'll be in touch to discuss moving you to a new plan.
                            </p>
                        </div>
                        <div className="panel panel-default panel-grey">
                            <p className="question">What about an annual discount?</p>
                            <p className="answer">
                                We're working on this - please
                                {' '}
                                <a href="mailto:support@bullettrain.io">get in touch</a>
                                {' '}
                                if this is important to you right now.
                            </p>
                        </div>
                        <div className="panel panel-default panel-grey">
                            <p className="question">Wait, what? This seems too cheap?</p>
                            <p className="answer">
                                We like to think of it as offering great value 🤪
                            </p>
                        </div>
                        <div className="text-center cta-container">
                            <h5>Didn't find an answer to your question?</h5>
                            <a onClick={this.feedback} className="pricing-cta blue">Get in touch</a>
                        </div>
                    </div>
                </div>
                <Footer className="homepage"/>
            </div>
        );
    }
};

module.exports = ConfigProvider(PricingPage);
