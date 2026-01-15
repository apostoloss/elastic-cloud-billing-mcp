# Elastic Cloud Billing MCP Server
Minimal Model Context Protocol (MCP) server exposing Elastic Cloud billing/usage data for LLM tooling.

## Motivation
- Fullfil cost tracking and stale environments cleanup needs (during experimentation and development phase of various projects) with the help of an LLM based editor.

_Side note: Any actions that can affect the current deployments in any way or create new have not been implemented intentionally. If you'd like such functionality drop me a note, consider contributing and/or sponsor it._

## Tools available

- **get_deployments**: Get the list of deployments.
- **get_deployment**: Get a specific deployment. Needs deployment_id.
- **get_items_costs**: Get costs broken down by environment/deployment for a date range
- **get_instances_costs(start_date: datetime, end_date: datetime)**: Get costs associated with all instances for a date range.
- **get_instance_costs**: Get costs for a single instance over a date range.
- **get_environment_cost**: Return total cost (ECU) for an environment in a period.
- **switch_account**: Switch between Elastic Cloud accounts (assuming there are several accounts configured).
- **get_current_account**: Return current active account info.
- **list_accounts**: List available accounts based on configured `.env` files.

## Configuring
In order to use it you need to have at least one enviroment file under `accounts` directory. The environment files need to start with `.env.` and end with the name you want to name that org_id with.
Example `.env.dev` which is also the default in the current configuration.
Other options include (Check `config.py`) :
- `accounts_dir` environment files for accounts directory (defaults to `accounts`)
- `elastic_base_url` elastic cloud base url (defaults to "https://api.elastic-cloud.com")
- `billing_base_url` billing base url ("https://billing.elastic-cloud.com")
- `default_account` the initial account that will be used during startup (defaults to `dev`)

In the account files you need to have the following variables set:
`ELASTIC_API_KEY`
`ELASTIC_ORG_ID`


## Quick Start
Edit and move `env.example` to `.env.dev` into `accounts` dir.

### Requirements
You need `uv` as it is set in current `mcp.json`. 
If you do not want to use it, update the json with the correct python environment (`requirement.txt` is not provided - yet.)

### Within IDE
Use `.cursor/mcp.json`(can be loaded in vscode as well)

### using a proxy
(You need `mcpo`)
Use mcpo like: `uvx mcpo --config .cursor/mcp.json --hot-reload --port 8080`
This will also give you the ability to check [swagger docs](http://0.0.0.0:8080/elastic-cloud-billing/docs) (assuming you run it locally)


## License
This project is licensed under the MIT License

## Sponsorship
None yet, please do reach out in case you would like to sponsor dev efforts or just say thanks.
