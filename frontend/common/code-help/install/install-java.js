import Utils from '../../utils/utils';

module.exports = ({ NPM_NODE_CLIENT, URL_CLIENT }) => `// Maven
${Utils.escapeHtml('<dependency>')}
${Utils.escapeHtml('<groupId>com.flagsmith</groupId>')}
${Utils.escapeHtml('<artifactId>flagsmith-java-client</artifactId>')}
${Utils.escapeHtml('<version>2.8</version>')}
</dependency>

// Gradle
implementation 'com.flagsmith:flagsmith-java-client:2.6'
`;
