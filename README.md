# Mimikatz Credentials Collector - Agent Plugin for Infection Monkey

## Introduction

Mimikatz Credentials Collector is an Agent Plugin for
[Infection Monkey](https://www.akamai.com/infectionmonkey) that
steals credentials from Windows Credential Manager using
[pypykatz](https://github.com/skelsec/pypykatz).

For more information, see the [Mimikatz Credentials Collector Plugin
documentation](https://techdocs.akamai.com/infection-monkey/docs/credential-collectors#mimikatz).

## Development
### Setting up the development environment

To create the resulting Mimikatz archive, follow these steps:

1. **Clone the Repository**

    ```sh
    $ git clone https://github.com/guardicode/mimikatz-credentials_collector.git
    $ cd mimikatz-credentials_collector
    ```

1. **Install development dependencies**

    This project uses [Poetry](https://python-poetry.org/) for managing
    dependencies and virtual environments, and
    [pre-commit](https://pre-commit.com/) for managing pre-commit hooks.

    ```sh
    $ pip install pre-commit poetry
    $ pre-commit install -t pre-commit
    $ poetry install
    ```

### Running the test suite

The test suite can be run with the following command:

```sh
poetry run pytest
```

### Building the plugin

To build the plugin, run the [Agent Plugin
Builder](https://github.com/guardicode/agent-plugin-builder/).

```sh
poetry run build_agent_plugin .
```

The build tool will create `Mimikatz-credentials_collector.tar`, which can be [installed in
the Monkey Island](https://techdocs.akamai.com/infection-monkey/docs/plugins).
