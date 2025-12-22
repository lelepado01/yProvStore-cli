# yProvStore CLI

**yProv CLI** is a command-line interface (CLI) tool that allows users to interact with the yProvStore backend service. It provides various commands to manage provenance documents, metadata, permissions, and blockchain records.

yProv is a joint project between [University of Trento](https://www.unitn.it) and [CMCC](https://www.cmcc.it).

## Table of Contents

- [yProvStore CLI](#yprovstore-cli)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Basic Command Structure](#basic-command-structure)
  - [Available Commands](#available-commands)
  - [Configuration](#configuration)
  - [Detailed Commands](#detailed-commands)

## Installation

To install the CLI and its dependencies, navigate to the repository root directory and run the following commands.

#### Linux and macOS

```bash
chmod +x prepare_cli.sh
source prepare_cli.sh
```

#### Windows
```bash
call prepare_cli.bat
```

This will set up the CLI environment by initiating the virtual environment and making the `yprov` command available in your terminal.

> **Note**: After you have finished using the CLI, you can deactivate the virtual environment by running `deactivate` in your terminal.

**Prepare the CLI before its usage:**

In general, remember to always run `source prepare_cli.sh` (or `call prepare_cli.bat` on Windows) before using the CLI to ensure that the environment is set up correctly.
This should be done not only when you first install the CLI, but also whenever you open a new terminal session where you want to use the CLI.


## Basic Command Structure

The basic structure of the CLI commands is as follows:

```bash
yprov <command> [options]
```

Where `<command>` is the specific action you want to perform, such as `auth`, `documents`, etc., and `[options]` are additional parameters for that command.

## Available Commands

```bash
yprov check
yprov auth signup
yprov auth login
yprov auth verify
yprov auth logout
yprov documents create --json-file <path/to/document.json> [--parent-pid <parent_pid>] [--compressed] [--trustworthy] [--<metadata_field> <value> ...]
yprov documents list [--page <page_number>] [--page-size <page_size>] [--updated-after <timestamp>] [--created-after <timestamp>]
yprov documents download <document_pid> [--output-folder <path>] [--output <file_path>] [--compressed] [--debug]
yprov documents permissions add <document_pid> --user-email <email> --permission-level <level>
yprov documents permissions list <document_pid>
yprov documents permissions delete <document_pid> --user-email <email>
yprov documents metadata get <document_pid>
yprov documents metadata update <document_pid> --key1 <key1> --key2 <value2>
yprov documents metadata schema
yprov documents graph list <document_pid> [--entity-types <type>] [--entity-ids <id>] [--is-element] [--is-relation] [--in-json] [--display-data] [--output <file_path>]
yprov documents graph subgraph <document_pid> --entity-id <entity_id> [--direction <direction>] [--output <file_path>]
yprov blockchain create --pid <pid> --url <url> --hash <hash> --owners <owners> [--timestamp <timestamp>] [--file <file_path>]
yprov blockchain read <pid>
yprov blockchain list --start-time <start_time> --end-time <end_time> [--format <table|json>]
yprov blockchain test
yprov pids list [--page <page_number>] [--page-size <page_size>]
yprov pids get <pid>
```

Each of these commands is better explained in the [CLI MANUAL](CLI_MANUAL.md).

However, you can also examine the help message for each command by running:

```bash
yprov <command> --help
```

-----

## Configuration

The CLI defaults to connecting to `http://127.0.0.1:8000`. You can specify a different API server URL in two ways:

1.  **Using the `--api-url` option:**

    ```bash
    yprov --api-url http://your-api-server.com:8000 check
    ```

2.  **Setting an environment variable:**

    ```bash
    export YPROV_API_URL="http://your-api-server.com:8000"
    ```
    > Or on Windows:
    > ```cmd
    > set YPROV_API_URL="http://your-api-server.com:8000"
    > ```

    You can then check the status of the API server with:

    ```bash
    yprov check
    ```

-----

## Detailed Commands

You can find detailed explanations and usage examples for each command in the [CLI MANUAL](CLI_MANUAL.md).
