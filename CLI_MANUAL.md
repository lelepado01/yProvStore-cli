# yProvStore CLI Manual

Here you can find detailed explanations and usage examples for each command available in the `yProvStore` CLI.

You can configure the API server URL using the `--api-url` option or the `YPROV_API_URL` environment variable as described in the [README](README.md#configuration).

## Table of Contents
- [Available Commands](#available-commands)
- [Authentication](#authentication)
- [Managing Documents](#managing-documents)
- [Managing Document Permissions](#managing-document-permissions)
- [Managing Document Metadata](#managing-document-metadata)
- [Graph Operations on Documents](#graph-operations-on-documents)
- [Blockchain Operations](#blockchain-operations)
- [Managing PIDs](#managing-pids)
- [Managing Artifacts](#managing-artifacts)
- [Troubleshooting CLI](#troubleshooting-cli)

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

You can also check the help message for each command at any level by running:

```bash
yprov <command> --help
```

## Authentication

First, you need to register and log in to get an access token. The token is stored locally and used for all authenticated requests.

  * **Sign up** for a new account.
    ```bash
    yprov auth signup
    ```
  * **Log in** to your account to get an access token.
    ```bash
    yprov auth login
    ```
  * **Verify** that your token is valid and see which user you are logged in as.
    ```bash
    yprov auth verify
    ```
  * **Log out** by deleting your local access token.
    ```bash
    yprov auth logout
    ```

-----


## Managing Documents

Once authenticated, you can create, list, and download provenance documents.

  * **Create a new document** from a JSON file or a JSON string (only one of these options is allowed at a time). You can also provide **initial metadata** at creation time using the same dynamic metadata field options available in the `documents metadata update` command. Any extra `--<field> <value>` pairs (after the declared options) are validated against the metadata schema and sent as a JSON object in the `document_metadata` query parameter.

    ```bash
  # From a file:
  yprov documents create --json-file examples/doc.json

  # Or from an inline JSON string:
  yprov documents create --value "{\"title\":\"My Doc\",\"owner_email\":\"me@example.com\"}"

  # With initial metadata (title & keywords) from JSON file:
  yprov documents create --json-file examples/doc.json --title "Initial Title" --keywords kw1 --keywords kw2

  # With initial metadata using comma-separated list and author field:
  yprov documents create --value '{"some":"data"}' --author "Jane Doe" --keywords "science,analysis"

  # For dict fields, use double underscore to specify nested keys:
  yprov documents create --json-file examples/doc.json --extra__custom_field "value" --extra__another_key "another value"

  # Refresh the metadata schema before applying metadata (if server changed):
  yprov documents create --json-file examples/doc.json --refresh-schema --title "New Title"
    ```

  You can also specify a parent document in either case:

    ```bash
    yprov documents create \
      --json-file examples/doc.json \
      --parent-pid <parent_pid_here>
    ```

  For enhanced trustworthiness, you can create a blockchain record alongside the document:

    ```bash
    # Create document with blockchain record for trustworthiness
    yprov documents create \
      --json-file examples/doc.json \
      --trustworthy

    # Or with both parent PID and blockchain record
    yprov documents create \
      --json-file examples/doc.json \
      --parent-pid <parent_pid_here> \
      --trustworthy
    ```

  For faster uploads of large documents, you can enable compression:

    ```bash
    # Upload with zstd compression to reduce transfer time
    yprov documents create \
      --json-file examples/doc.json \
      --compressed
    ```

  **Options:**

  - `--json-file`: Path to a JSON file containing the document data.
  - `--value`: A JSON string containing the document data (mutually exclusive with `--json-file`).
  - `--parent-pid`: PID of the parent document, if any.
  - `--compressed`: Compress the document data using zstd before uploading to reduce transfer size (requires `zstandard` library).
  - `--trustworthy`: Also create a record of the document on the blockchain for enhanced trustworthiness and immutable provenance tracking.
  - `--refresh-schema`: Force re-download of the metadata schema before validating dynamic metadata options.
  - `--<metadata_field> <value>`: Any extra options matching fields defined in the metadata schema (e.g. `--title`, `--description`, `--keywords`, `--author`). Repeat list-type fields multiple times or pass comma-separated values (e.g. `--keywords kw1 --keywords kw2` or `--keywords "kw1,kw2"`). Empty string (`""`) sets a field to empty; for list fields an empty string results in an empty list.
  - `--<dict_field>__<key> <value>`: For dict-type fields (e.g. `extra`), use double underscore syntax to set nested keys (e.g. `--extra__custom_field "value"`). Pass an empty string (`""`) to delete a specific key from the dict.

  **Notes:** 
  - Initial metadata is sent via the `document_metadata` query parameter as a JSON object constructed from the dynamic metadata flags.
  - Unknown metadata fields are ignored with a warning.
  - To use the `--trustworthy` option, you need to configure the blockchain connection environment variables as described in the [Blockchain Operations](#blockchain-operations) section. If the blockchain configuration is missing or invalid, the document record creation will fail with an appropriate error message.
  - Use `--refresh-schema` if you recently changed metadata schema server-side and want to ensure the CLI uses the latest.

  * **List all available documents** (with pagination).

    ```bash
    yprov documents list [--page <page_number>] [--page-size <page_size>] [--updated-after <timestamp>] [--created-after <timestamp>]
    ```

    - `--page <page_number>`: Page number to retrieve (zero-indexed, default: 0).
    - `--page-size <page_size>`: Number of documents per page (default: 10).
    - `--updated-after <timestamp>`: Only return documents updated after this timestamp (ISO 8601 format, e.g., `2024-06-01T00:00:00Z` or `2024-06-01`).
    - `--created-after <timestamp>`: Only return documents created after this timestamp (ISO 8601 format, e.g., `2024-06-01T00:00:00Z` or `2024-06-01`).

    Examples:

    * List the first page (default 10 items):

      ```bash
      yprov documents list
      ```

    * List the third page (page 2, zero-indexed) with 50 items per page:

      ```bash
      yprov documents list --page 2 --page-size 50
      ```

    * List documents updated after June 1, 2024:

      ```bash
      yprov documents list --updated-after 2024-06-01
      ```

    * List documents updated after a specific timestamp:

      ```bash
      yprov documents list --updated-after 2024-06-01T00:00:00Z
      ```

    * List documents created after June 1, 2024:

      ```bash
      yprov documents list --created-after 2024-06-01
      ```

    * List documents created after a specific timestamp:

      ```bash
      yprov documents list --created-after 2024-06-01T00:00:00Z
      ```

  * **Download a document's file**.

    ```bash
    Usage: yprov documents download [OPTIONS] PID

    Download a document file by its PID.

    Options:
      -o, --output FILE                 Full path to save the file (e.g.,
                                        'my_dir/my_doc.json'). This overrides --output-folder.
      --output-folder DIRECTORY         Folder to save the file in. The filename will
                                        default to the document's PID.
      --compressed                      Request compressed download from server to reduce
                                        transfer size (requires zstd).
      --debug                           Enable debug output for troubleshooting compression issues.
      --trustworthy / --no-trustworthy  Verify SHA256: recompute the local file hash and
                                        compare it with the hash stored in the yProvStore database
                                        and the one on the blockchain. Defaults to --no-trustworthy.
    ```

    Notes:
    - `--output` takes precedence over `--output-folder`.
    - If `PID` uses the `prefix/pid` form, the CLI will create a `prefix/` subfolder (inside the chosen output folder or the current directory) and save the file as `prefix/pid.json`.
    - The `--compressed` option requests the server to send compressed data (zstd format), which is automatically decompressed before saving. This can significantly reduce download time for large documents.
    - The `--debug` option provides detailed information about the download process, including compression status and data inspection.
    - When `--trustworthy` is passed the command will:
       1. recompute the downloaded file's SHA-256,
       2. fetch the DB hash from `GET /documents/{pid}`,
       3. read the blockchain-stored hash via the Fabric connector (! this requires proper blockchain configuration, see the [Blockchain Operations](#blockchain-operations) section),
       4. print a summary and indicate whether the three hashes match.

    Examples:

    * Save to the current directory (e.g., `<pid>.json`):

      ```bash
      yprov documents download <your_document_pid>
      ```

    * Save to a specific folder:

      ```bash
      yprov documents download <your_document_pid> --output-folder /path/to/downloads
      ```

    * Save with a specific file name and path:

      ```bash
      yprov documents download <your_document_pid> --output /path/to/my_doc.json
      ```

    * Download with compression for faster transfer:

      ```bash
      yprov documents download <your_document_pid> --compressed
      ```

    * Download with compression and debug information:

      ```bash
      yprov documents download <your_document_pid> --compressed --debug
      ```

    * Download and verify hash against DB and blockchain:

      ```bash
      yprov documents download <your_document_pid> --trustworthy
      ```

    * Combine compression with hash verification:

      ```bash
      yprov documents download <your_document_pid> --compressed --trustworthy
      ```

    * Force skip verification (explicit) (is the default behavior):

      ```bash
      yprov documents download <your_document_pid> --no-trustworthy
      ```


  * **List all available documents**.

    ```bash
    yprov documents list
    ```

  * **Get detailed information** for a specific document by its PID.

    ```bash
    yprov documents get <your_document_pid>
    ```

  * **Download a document's file**.

      ```bash
      Usage: yprov documents download [OPTIONS] PID
      
      Download a document file by its PID.
      
      Options:
        -o, --output FILE          Full path to save the file (e.g.,
                                  'my_dir/my_doc.json'). This overrides --output-
                                  folder.
        --output-folder DIRECTORY  Folder to save the file in. The filename will
                                  default to the document's PID.
      ```
      
      * Save to the current directory (e.g., `<pid>.json`):
      
        ```bash
        yprov documents download <your_document_pid>
        ```
      * Save to a specific folder:
        ```bash
        yprov documents download <your_document_pid> --output-folder /path/to/downloads
        ```
      * Save with a specific file name and path:
        ```bash
        yprov documents download <your_document_pid> --output /path/to/my_doc.json
        ```

-----

## Managing Document Permissions

You can grant or view permissions on documents. Internally, all permissions live on the *first version* of a document—adding or listing against any version will target that root document.

* **Add a permission**

  ```bash
  yprov documents permissions add <prefix/id> \
    --user-email user@example.com \
    --permission-level write
  ```

  Notes:

  * PID **must** be in `prefix/id` form.
  * Permissions are always stored on the first version; granting on v2 or v3 still writes to v1.
  * The first version document must already reside on this server instance.
  * Although `read` is supported by the service, setting `read` on already‑public docs may result in an error.

- **List permissions**

  ```bash
  yprov documents permissions list <pid>
  ```

  `<pid>` must be `prefix/id`. This shows every user and their permission level on that document’s first version.

- **Delete a permission**

  ```bash
  yprov documents permissions delete <prefix/id> --user-email user@example.com
  ```

  This command deletes the permission for the specified user on the document's first version. The `<prefix/id>` can be provided in the same way as in the list command.

  You must be the owner of the first version of the document to delete permissions. If you are not the owner, you will receive a `403 Forbidden` error.

-----

## Managing Document Metadata


You can manage metadata for documents, including retrieving and updating it.

- **Get metadata for a document**

  ```bash
  yprov documents metadata get <document_pid>
  ```

  This command retrieves the metadata associated with the specified document PID.

- **Update metadata for a document**

  ```bash
  yprov documents metadata update <document_pid> --key <value>
  ```

  This command updates the metadata for the specified document PID.
  You can specify multiple key-value pairs to update multiple metadata fields at once.
  To set a list field, use multiple invocations of the same option, or pass a list as a comma-separated string.
  For example:

  ```bash
  yprov documents metadata update <document_pid> --title "New Title" --keywords keyword1 --keywords keyword2
  # or
  yprov documents metadata update <document_pid> --title "New Title" --keywords "keyword1,keyword2"

  # This command will empty both title and keywords:
  yprov documents metadata update <document_pid> --title "" --keywords ""

  # For dict fields (e.g., extra), use double underscore to specify nested keys:
  yprov documents metadata update <document_pid> --extra__custom_field "value"
  yprov documents metadata update <document_pid> --extra__key1 "value1" --extra__key2 "value2"

  # To delete a dict key, pass an empty string:
  yprov documents metadata update <document_pid> --extra__custom_field ""
  ```
  
  - The PID must be fully qualified (prefix/id).
  - Only passed fields will be updated; existing fields not specified will remain unchanged.
  - Before updating, the command will validate the provided fields against the metadata schema fetched from the server.
  - Fields not defined in the schema will be ignored.
  - To set an empty field, use an empty string.
  - To set a list field, use multiple invocations of the same option.
  - To update a list field, you need to pass the entire list each time.
  - For dict fields (e.g., `extra`), use `--<dict_field>__<key> "value"` syntax to set nested keys.
  - To delete a dict key, pass an empty string as the value (e.g., `--extra__key ""`).
  - If no fields are provided, the command will exit with a warning.
  - To update metadata for a document, you must be the owner of the document or have write permissions on it.

- **Get metadata schema**

  You can retrieve the metadata schema, which defines the structure and fields of the metadata.

  ```bash
  yprov documents metadata schema
  ```

  The schema defines the structure and fields that can be used in document metadata.

  Example output:

  ```
  > yprov documents metadata schema
                              Document Metadata Schema
  ┌─────────────┬──────────────┬──────────┬────────────────────────────────────────┐
  │ Field       │ Type         │ Required │ Example                                │
  ├─────────────┼──────────────┼──────────┼────────────────────────────────────────┤
  │ title       │ string       │ No       │ Sample Document Title                  │
  │ description │ string       │ No       │ This is a sample document description. │
  │ keywords    │ list[string] │ No       │ ['keyword1', 'keyword2']               │
  └─────────────┴──────────────┴──────────┴────────────────────────────────────────┘
  ```

-----

## Graph Operations on Documents

You can explore and analyze the provenance graph structure of documents. Graph operations allow you to list elements or extract a self-contained subgraph by tracing relationships from specific starting points.

* **List graph elements**

  ```bash
  yprov documents graph list <prefix/id> [OPTIONS]
  ```

  This command lists all elements in a provenance document's graph, including entities, agents, activities, and relationships.

  Options:

  * `--entity-types, -t`   Filter by entity types (can be used multiple times). Examples: `entity`, `agent`, `activity`, `wasDerivedFrom`, `wasGeneratedBy`
  * `--entity-ids, -e`     Filter by specific entity IDs (can be used multiple times)
  * `--is-element, -ie`    Filter by whether the entity is an element (boolean flag)
  * `--is-relation, -ir`   Filter by whether the entity is a relation (boolean flag)
  * `--in-json, -j`        Output results in JSON format with complete data
  * `--display-data, -d`   Include the data field in the console table output
  * `--output, -o`         Save results to a file path (writes complete JSON data)

  Examples:

  * List all graph elements for a document:

    ```bash
    yprov documents graph list myprefix/1234
    ```

  * Filter by specific entity types:

    ```bash
    yprov documents graph list myprefix/1234 --entity-types entity --entity-types agent
    # or, shorter:
    yprov documents graph list myprefix/1234 -t entity -t agent
    ```

  * Filter by entity which are elements:

    ```bash
    yprov documents graph list myprefix/1234 --is-element
    # or, shorter:
    yprov documents graph list myprefix/1234 -ie
    ```

  * Filter by entity which are relations:

    ```bash
    yprov documents graph list myprefix/1234 --is-relation
    # or, shorter:
    yprov documents graph list myprefix/1234 -ir
    ```

  * Filter by entity IDs and display data in the console:

    ```bash
    yprov documents graph list myprefix/1234 --entity-ids "my_entity_1" --display-data
    ```

  * Save results to a JSON file:

    ```bash
    yprov documents graph list myprefix/1234 --output /path/to/graph_elements.json
    ```

  * Get JSON output in the console:

    ```bash
    yprov documents graph list myprefix/1234 --in-json
    ```

  Notes:

  * The PID **must** be in `prefix/id` format.
  * The command displays a table with columns: ID, Type, Group, Is Element, Is Relation.
  * Use `--display-data` to see the actual data content of each element in the console.
  * Multiple filters can be combined (e.g., both entity types and entity IDs).
  * The output includes any warnings from the server and a total count of elements found.


-----

  * **Extract a subgraph**

    ```bash
    yprov documents graph subgraph <prefix/id> [OPTIONS]
    ```

    This command extracts a self-contained subgraph by tracing the provenance relationships from one or more starting entity IDs. The result is a valid **PROV-JSON** document.

    **Options:**

      * `--entity-id, -e` **[Required]** An entity ID to start the traversal from (can be used multiple times).
      * `--direction, -d` The direction for traversal: `forward`, `backward`, or `both` (default: `both`).
      * `--output, -o` Save the resulting PROV-JSON subgraph to a file.

    **Examples:**

      * Extract a subgraph tracing **forward** from a single entity and save it:

        ```bash
        yprov documents graph subgraph myprefix/1234 --entity-id "my_activity_1" --direction forward --output subgraph.json
        ```

      * Get a **backward** trace from an entity, printing the JSON to the console:

        ```bash
        yprov documents graph subgraph myprefix/1234 -e "final_product" -d backward
        ```

      * Trace in **both** directions from multiple starting points:

        ```bash
        yprov documents graph subgraph myprefix/1234 -e "entity_A" -e "entity_B"
        ```

    **Notes:**

      * You **must** provide at least one `--entity-id`.
      * The output is always a PROV-JSON document, not a table.
      * If the resulting JSON is too large to display in the console, it will be automatically saved to a file named `subgraph_<prefix>_<id>.json`.
      * Any warnings from the server are always displayed.

-----

## Blockchain Operations

The `blockchain` command group provides functionality to interact with blockchain networks for document provenance storage. These commands allow you to create, read, and query documents stored on the blockchain, providing an immutable record of document provenance.

**Prerequisites:**

Before using blockchain operations, ensure you have set the required environment variables for your blockchain network connection:

- `CONNECTOR_PEER_TLSCERT_PATH` - Path to the peer TLS certificate
- `CONNECTOR_USR_PKEY_PATH` - Path to the user private key
- `CONNECTOR_PEER_ENDPOINT` - Blockchain peer endpoint
- `CONNECTOR_USR_CERT_PATH` - Path to the user certificate  
- `CONNECTOR_PEER_MSP_ID` - Membership Service Provider ID
- `CONNECTOR_PEER_HOSTNAME` - Peer hostname (optional, defaults to peer endpoint)

* **Create a document on the blockchain**

  ```bash
  yprov blockchain create --pid <pid> --url <url> --hash <hash> --owners <owners> [--timestamp <timestamp>]
  ```

  Create a new document record on the blockchain with the specified provenance information.

  **Options:**

  * `--pid` - Unique identifier for the document (required)
  * `--url` - URL where the document can be accessed (required)
  * `--hash` - Hash of the document content (required)
  * `--owners` - Comma-separated list of document owners (required)
  * `--timestamp` - Document timestamp in ISO-8601 format (optional, defaults to current time)
  * `--file` - Path to a JSON file containing document data (alternative to individual options)

  **Examples:**

  * Create a document with command-line options:

    ```bash
    yprov blockchain create \
      --pid "prefix/example-doc" \
      --url "https://example.com/documents/example-doc.json" \
      --hash "sha256:abc123def456" \
      --owners "user1@example.com,user2@example.com"
    ```

  * Create a document from a JSON file:

    ```bash
    yprov blockchain create --file document_data.json
    ```

    The JSON file should contain:

    ```json
    {
      "pid": "prefix/example-doc",
      "url": "https://example.com/documents/example-doc.json",
      "hash": "sha256:abc123def456",
      "owners": ["user1@example.com", "user2@example.com"],
      "timestamp": "2024-01-01T12:00:00Z"
    }
    ```

  **Notes:**

  * Cannot use both `--file` and individual options simultaneously
  * Owners list is automatically normalized (duplicates removed)
  * If timestamp is not provided, current time will be used

* **Read a document from the blockchain**

  ```bash
  yprov blockchain read <pid>
  ```

  Retrieve and display a document's information from the blockchain by its PID.

  **Examples:**

  * Read a document:

    ```bash
    yprov blockchain read "prefix/example-doc"
    ```

  * The command displays document information in a formatted table and offers an option to view the raw JSON data.

* **List documents by time interval**

  ```bash
  yprov blockchain list --start-time <start_time> --end-time <end_time> [--format <format>]
  ```

  Query and list documents created within a specific time interval.

  **Options:**

  * `--start-time` - Start time for the query (ISO-8601 format or timestamp) (required)
  * `--end-time` - End time for the query (ISO-8601 format or timestamp) (required)
  * `--format` - Output format: `table` (default) or `json`

  **Examples:**

  * List documents in a date range with table format:

    ```bash
    yprov blockchain list \
      --start-time "2024-01-01T00:00:00Z" \
      --end-time "2024-01-31T23:59:59Z"
    ```

  * List documents with JSON output:

    ```bash
    yprov blockchain list \
      --start-time "1640995200000" \
      --end-time "1672531200000" \
      --format json
    ```

  **Notes:**

  * Time can be provided in ISO-8601 format or as Unix timestamps
  * Table format truncates long values for readability
  * JSON format provides complete document data

* **Test blockchain connection**

  ```bash
  yprov blockchain test
  ```

  Test the connection to the blockchain network by creating, reading, and querying test documents.

  **Examples:**

  ```bash
  yprov blockchain test
  ```

  **Notes:**

  * This command will create actual test documents on the blockchain
  * Tests document creation, reading, and interval querying functionality
  * Displays current environment variable values for debugging
  * Use this command to verify your blockchain configuration before production use

**Error Handling:**

All blockchain commands provide detailed error messages and will display the current status of required environment variables when connection issues occur. If you encounter authentication or connection errors, verify that all required environment variables are properly set and that your certificates and keys are valid.

-----

## Managing PIDs

`yProvStore` additionally provides some proxy methods to retrieve PID records directly from the underlying PID service (Handle System).

The `pids` group lets you list and retrieve PID records from your PID service.

* **List PIDs** (with optional pagination)

  ```bash
    yprov pids list [OPTIONS]
  ```

  Options:

  * `--page INTEGER`       Page number (zero‑indexed). Default: `0`
  * `--page-size INTEGER`   Number of items per page. Default: `10`

  Examples:

  * List the first page (10 items):

    ```bash
    yprov pids list
    ```
  * List page 2 (zero‑indexed, i.e. the third page) with 50 items per page:

    ```bash
    yprov pids list --page 2 --page-size 50
    ```

- **Get a PID record** (by prefix/id)

  ```bash
  yprov pids get <PID>
  ```

  Examples:

  * Retrieve a record with an explicit prefix:

    ```bash
    yprov pids get myprefix/1234
    ```


## Managing Artifacts

`yProvStore` allows you to upload, download, and manage artifact files (e.g., data files, scripts, binaries) alongside your provenance documents. Each artifact is assigned a unique PID and can be referenced in your provenance records.

The `artifacts` group provides commands to interact with artifact storage.

* **List artifacts** (with optional pagination and filtering)

  ```bash
  yprov artifacts list [OPTIONS]
  ```

  Options:

  * `--page INTEGER`          Page number (zero-indexed). Default: `0`
  * `--page-size INTEGER`     Number of artifacts per page. Default: `10`
  * `--updated-after TEXT`    List only artifacts updated after this ISO 8601 datetime
  * `--created-after TEXT`    List only artifacts created after this ISO 8601 datetime
  * `--pid TEXT`              Filter by a specific artifact PID

  Examples:

  * List the first page of artifacts:

    ```bash
    yprov artifacts list
    ```

* **Upload an artifact**

  ```bash
  yprov artifacts upload <FILE_PATH> [OPTIONS]
  ```

  Options:

  * `--filename TEXT`   Custom filename to use for the artifact (defaults to original filename)

  Examples:

  * Upload a file with the original filename:

    ```bash
    yprov artifacts upload ./my_artifact.tar.gz
    ```

  * Upload a file with a custom filename:

    ```bash
    yprov artifacts upload ./data.csv --filename "experiment_data.csv"
    ```

* **Download an artifact**

  ```bash
  yprov artifacts download <PID> [OPTIONS]
  ```

  Options:

  * `-o, --output PATH`         Full path to save the file (overrides --output-folder)
  * `--output-folder PATH`      Folder to save the file in (filename determined from server)
  * `--verify / --no-verify`    Verify SHA-256 hash after download. Default: `False`

  Examples:

  * Download an artifact to the current directory:

    ```bash
    yprov artifacts download 21.T11961/abc123
    ```

  * Download to a specific location:

    ```bash
    yprov artifacts download abc123 -o ./downloads/artifact.tar.gz
    ```

  * Download with hash verification:

    ```bash
    yprov artifacts download abc123 --output-folder ./downloads --verify
    ```

* **Get artifact information**

  ```bash
  yprov artifacts get <PID>
  ```

  Examples:

  * Get detailed information about an artifact:

    ```bash
    yprov artifacts get 21.T11961/abc123
    ```


## Troubleshooting CLI

If you encounter this issue when running the CLI:

```
command not found: yprov
```

It means that the `yprov` command is not recognized in your terminal. This can happen if the virtual environment is not activated or if the CLI was not set up correctly.
To resolve this, ensure you have run `source prepare_cli.sh` script as described in the [Installation](#installation) section.

