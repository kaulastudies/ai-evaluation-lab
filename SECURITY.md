# Security and Data Handling

This public repository contains only public or synthetic examples.

Never commit API keys, customer prompts, patient information, private Handshake/Fieldborne task content, proprietary benchmarks, confidential evaluation results, or credentials.

## Provider boundary

Free/developer tiers can have different retention or model-improvement terms from paid plans. Before using a provider with non-public material:

1. review its current data-use and retention terms;
2. determine whether prompts/responses can be used for training or improvement;
3. choose an appropriate paid/enterprise/no-retention option where required;
4. document the provider and policy version in the private project workspace.

## Secrets

Use environment variables. `.env` is ignored by git.

If a secret is ever committed, deleting the file is not enough: revoke/rotate the credential and clean history when necessary.
