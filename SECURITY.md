# Security policy

## Supported version

The latest version on the default branch receives security fixes.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability or exposed secret. Contact the repository owner privately through the GitHub profile and include reproduction steps, affected files and potential impact. Allow reasonable time for investigation before disclosure.

## Safe operation

- Replace demonstration database credentials before deployment.
- Keep `.env` local and use a secret manager in hosted environments.
- Store Snowflake passwords or key-pair material in a secret manager; never commit them or place them in YAML defaults.
- Restrict database network access and grant the ETL account only required schema privileges.
- Review dependency alerts and update pinned packages through tested pull requests.
- Treat all repository datasets as synthetic; do not mix them with production or personal data.
