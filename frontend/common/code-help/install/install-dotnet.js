import Utils from '../../utils/utils';

module.exports = ({ NPM_NODE_CLIENT, URL_CLIENT }) => `// Package Manager
PM> Install-Package Flagsmith -Version 4.0.0

// .NET CLI
dotnet add package Flagsmith --version 4.0.0

// PackageReference
${Utils.escapeHtml('<PackageReference Include="Flagsmith" Version="4.0.0" />')}

// Paket CLI
paket add Flagsmith --version 4.0.0
`;
