# SonarCloud Setup Guide

This document explains how to set up SonarCloud for the Docker MCP AI Stack project.

## Prerequisites

1. A SonarCloud account (sign up at <https://sonarcloud.io>)
2. Admin access to this GitHub repository
3. Access to repository secrets configuration

## Setup Steps

### 1. Create SonarCloud Organization

1. Log in to SonarCloud
2. Click on "+" in the top navigation
3. Select "Create Organization"
4. Choose "From GitHub" and authorize SonarCloud
5. Select your organization/username
6. Note down the organization key (you'll need this)

### 2. Import Your Project

1. In SonarCloud, click "+" and select "Analyze new project"
2. Select this repository (`docker-mcpai-stack`)
3. Click "Set up"
4. Choose "GitHub Actions" as the analysis method

### 3. Configure Repository Secrets

In your GitHub repository, go to Settings > Secrets and variables > Actions, and add:

- `SONAR_TOKEN`: Get this from SonarCloud > My Account > Security > Generate Token
- The `GITHUB_TOKEN` is automatically provided by GitHub Actions

### 4. Update Configuration

1. In `sonar-project.properties`, replace `your-org-key` with your actual SonarCloud organization key
2. Update the `sonar.projectKey` if needed (should match your SonarCloud project key)

### 5. Quality Gate Configuration

The project is configured to wait for the quality gate results. You can customize quality gates in SonarCloud:

1. Go to your project in SonarCloud
2. Navigate to "Quality Gates"
3. Customize conditions as needed

## Configuration Files

- `sonar-project.properties`: Main SonarCloud configuration
- `.github/workflows/ci.yml`: CI pipeline with SonarCloud integration

## Troubleshooting

### Common Issues

1. **Authentication Error**: Ensure `SONAR_TOKEN` is correctly set in repository secrets
2. **Organization Not Found**: Verify the organization key in `sonar-project.properties`
3. **Project Key Conflicts**: Ensure the project key is unique across SonarCloud

### Coverage Reports

The CI pipeline runs tests with coverage and uploads the results to SonarCloud. Coverage reports are
generated in XML format for SonarCloud consumption.

## Integration Benefits

- Automatic code quality analysis on every push
- Pull request decoration with quality metrics
- Security hotspot detection
- Code coverage tracking
- Quality gate enforcement

For more information, visit the [SonarCloud documentation](https://docs.sonarcloud.io/).
