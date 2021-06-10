const ServiceLevelAgreement = props => (
    <div className="legal-container">
        <div className="container">
            <h2>Service Level Agreement</h2>
            <p>
                This Flagsmith Service Level Agreement (
                <b>“SLA”</b>
                ) between Flagsmith Ltd (
                <b>"Flagsmith"</b>
                ,
                <b>“us”</b>
                {' '}
                or
                <b>“we”</b>
                ) and users of the Flagsmith Services (
                <b>“you”</b>
                ) governs the use of Flagsmith Services under the provisions of the
                <Link to="/legal/tos">Flagsmith Terms of Service</Link>
                {' '}
                (the
                <b>“Terms”</b>
                ).
            </p>
            <p>Unless otherwise provided herein, this SLA is subject to the provisions of the Terms.</p>

            <ol className="sla-list">
                <li>
                    <h5>Flagsmith Service Commitment: 99.95% Uptime</h5>
                    <p>
                        Flagsmith will use commercially reasonable efforts to ensure your Flagsmith Services are
                        running in Dedicated Environments available with a Monthly Uptime Percentage of at least 99.95%
                        during any monthly billing cycle (the
                        <b>“Service Commitment”</b>
                        ). Subject to the SLA Exclusions, if we do not meet the Service Commitment, you will be eligible
                        to receive a Service Credit.
                    </p>
                    <p>
A Monthly Uptime Percentage of 99.95% means that we guarantee you will experience no more than
                        21.56 min/month of Unavailability.
                    </p>
                </li>
                <li>
                    <h5>Definitions</h5>
                    <p>
                        <b>“Maintenance”</b>
                        {' '}
                        means scheduled Unavailability of Flagsmith Services, as announced by us prior to Bullet
                        Train Services becoming Unavailable.
                    </p>
                    <p>
                        <b>“Monthly Uptime Percentage”</b>
                        {' '}
                        is calculated by subtracting from 100% the percentage of minutes during the month in which
                        Flagsmith Services were Unavailable. Monthly Uptime Percentage measurements exclude downtime
                        resulting directly or indirectly from any SLA Exclusion.
                    </p>
                    <p>
                        <b>“Service Credit”</b>
                        {' '}
                        means a credit denominated in US dollars, calculated as set forth below, that we may credit back
                        to an eligible account.
                    </p>
                    <p>
                        <b>“Unavailable”</b>
                        {' '}
                        and
                        {' '}
                        <b>“Unavailability”</b>
                        {' '}
                        mean, for app services and databases, when your service or database is not running or not
                        reachable due to Flagsmith's fault. This excludes reasons where the fault lies with
                        Amazon Web Services.
                    </p>
                </li>
                <li>
                    <h5>Service Commitments and Service Credits</h5>
                    <p>
Service Credits are calculated as a percentage of the total charges due on your Flagsmith
                        invoice for the monthly billing cycle in which the Unavailability occurred, applied
                        proportionally to the Services that were Unavailable, in accordance with the schedule below:
                    </p>
                    <ul>
                        <li>
For Monthly Uptime Percentage less than 99.95% but equal to or greater than 99.0%, you will
                            be eligible for a Service Credit of 10% of the charges attributable to the affected
                            resources
                        </li>
                        <li>
For Monthly Uptime Percentage less than 99.0%, you will be eligible for a Service Credit of
                            30% of the charges attributable to the affected resources
                        </li>
                    </ul>
                    <p>
For example, if you have an app container that is Unavailable for 25 minutes, you would be
                        eligible for a Service Credit for 10% of that container’s usage for the month.
                    </p>
                    <p>
We will apply any Service Credits only against future payments for the Services otherwise due
                        from you. At our discretion, we may issue the Service Credit to the credit card you used to pay
                        for the billing cycle in which the Unavailability occurred. Service Credits will not entitle you
                        to any refund or other payment from Bullet Train Ltd. A Service Credit will be applicable
                        and issued only if the credit amount for the applicable monthly billing cycle is greater than
                        one dollar ($1 USD). Service Credits may not be transferred or applied to any other account.
                    </p>
                </li>
                <li>
                    <h5>Sole Remedy</h5>
                    <p>
Unless otherwise provided in the Terms, your sole and exclusive remedy for any unavailability,
                        non-performance, or other failure by us to provide the Services is the receipt of a Service
                        Credit (if eligible) in accordance with the terms of this SLA.
                    </p>
                </li>
                <li>
                    <h5>Credit Request and Payment Procedures</h5>
                    <p>
To receive a Service Credit, you must submit a claim by emailing support@solidstategroup.com. To
                        be eligible, the credit request must be received by us by the end of the second billing cycle
                        after which the incident occurred and must include:
                    </p>
                    <ul>
                        <li>the words “Flagsmith SLA Credit Request” in the subject line;</li>
                        <li>the dates and times of each Unavailability incident that you are claiming;</li>
                        <li>the account handle(s); and</li>
                        <li>
logs that document the errors and corroborate your claimed outage (any confidential or
                            sensitive information in these logs should be removed or replaced with asterisks).
                        </li>
                    </ul>
                    <p>
If the Monthly Uptime Percentage of such request is confirmed by us and is less than the Service
                        Commitment, then we will issue the Service Credit to you within one billing cycle following the
                        month in which your request is confirmed by us. Your failure to provide the request and other
                        information as required above will disqualify you from receiving a Service Credit.
                    </p>
                </li>
                <li>
                    <h5>SLA Exclusions</h5>
                    <p>The Service Commitment does not apply to any Unavailability:</p>
                    <ol>
                        <li>That results from a suspension or Remedial Action, as described in the Terms;</li>
                        <li>
Caused by factors outside of our reasonable control, including any force majeure event,
                            Internet access, or problems beyond the demarcation point of the Flagsmith network;
                        </li>
                        <li>That results from any actions or inactions of you or any third party;</li>
                        <li>
That results from the equipment, software or other technology of you or any third party
                            (other than third party equipment within our direct control);
                        </li>
                        <li>
That results from failures of Amazon Web Services not attributable to Unavailability; or
                        </li>
                        <li>That results from any Maintenance.</li>
                    </ol>
                    <p>
If availability is impacted by factors other than those used in our Monthly Uptime Percentage
                        calculation, then we may issue a Service Credit considering such factors at our discretion.
                    </p>
                </li>

            </ol>

        </div>
    </div>
);

ServiceLevelAgreement.displayName = 'ServiceLevelAgreement';
export default ServiceLevelAgreement;
