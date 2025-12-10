# GenFilesMCP 🧩

GenFilesMCP is a Model Context Protocol (MCP) server that generates PowerPoint, Excel, Word, or Markdown files from user requests and chat context, then uploads them to Azure Blob Storage. This MCP executes Python templates to produce files and provides time-limited SAS URLs for secure file access and sharing. Additionally, it supports analyzing and reviewing existing Word documents by extracting their structure and adding comments for corrections, grammar suggestions, or idea enhancements.

## Table of Contents

- [Features](#features)
- [Status](#status)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Option 1: Using Pre-built Docker Image (Recommended)](#option-1-using-pre-built-docker-image-recommended)
  - [Option 2: Building from Source](#option-2-building-from-source)
  - [Option 3: Docker Compose](#option-3-docker-compose)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [MCP Configuration in Open Web UI](#mcp-configuration-in-open-web-ui)
- [Setup for Document Generation and Review Features](#setup-for-document-generation-and-review-features)
  - [Knowledge Base and Permissions](#knowledge-base-and-permissions)
  - [MCP Server Document Upload Settings](#mcp-server-document-upload-settings)
- [Usage Examples](#usage-examples)
  - [Example 1: Generating a DOCX file](#example-1-generating-a-docx-file)
  - [Example 2: Reviewing a DOCX file with comments](#example-2-reviewing-a-docx-file-with-comments)
- [Star History](#star-history)

## Features

- **File Generation**: Creates files in multiple formats (PowerPoint, Excel, Word, Markdown) from user requests.
- **FastMCP Server**: Receives and processes generation requests via a FastMCP server.
- **Python Templates**: Uses customizable Python templates to generate files with specific structures.
- **Azure Blob Storage**: Automatically uploads generated files to Azure Blob Storage with time-limited SAS URLs for secure sharing and access.
- **Document Review**: Analyzes existing Word documents and adds structured comments for corrections, grammar suggestions, or idea enhancements.
- **Flexible Authentication**: Supports both connection string and Azure managed identity authentication.
- **Configurable Access Control**: Control file access duration with configurable SAS URL expiry times.

## Status

This is an **Azure Blob Storage only** version of GenFilesMCP. All generated and reviewed files are uploaded exclusively to Azure Blob Storage with time-limited SAS URLs for secure access.

> **Note:** This version does not integrate with Open Web UI's knowledge base. Files are stored only in Azure Blob Storage.

## Prerequisites

- **Docker** installed on your system
- **Azure Storage Account** with either:
  - Connection string (for connection string authentication), OR
  - Managed identity configured (for Azure-hosted deployments)

## Installation

### Option 1: Using Pre-built Docker Image (Recommended)

Pull the pre-built Docker image from GitHub Container Registry:

```bash
docker pull ghcr.io/baronco/genfilesmcp:latest
```

Run the container with connection string authentication:

```bash
docker run -d --restart unless-stopped -p 8015:8015 \
  -e PORT=8015 \
  -e AZURE_STORAGE_ENABLED=true \
  -e AZURE_CONNECTION_STRING="your-connection-string-here" \
  -e AZURE_CONTAINER_NAME=genfilesmcp \
  -e AZURE_SAS_EXPIRY_HOURS=24 \
  --name gen_files_mcp \
  ghcr.io/baronco/genfilesmcp:latest
```

Or with managed identity authentication (for Azure-hosted deployments):

```bash
docker run -d --restart unless-stopped -p 8015:8015 \
  -e PORT=8015 \
  -e AZURE_STORAGE_ENABLED=true \
  -e AZURE_USE_MANAGED_IDENTITY=true \
  -e AZURE_ACCOUNT_NAME=youraccount \
  -e AZURE_CONTAINER_NAME=genfilesmcp \
  -e AZURE_SAS_EXPIRY_HOURS=24 \
  --name gen_files_mcp \
  ghcr.io/baronco/genfilesmcp:latest
```

### Option 2: Building from Source

If you need to build the image yourself:

1. Clone the repository:

```bash
git clone https://github.com/Baronco/GenFilesMCP.git
cd GenFilesMCP
```

2. Build the Docker image:

```bash
docker build -t genfilesmcp .
```

3. Run the container (with connection string auth):

```bash
docker run -d --restart unless-stopped \
  -p 8015:8015 \
  -e PORT=8015 \
  -e AZURE_STORAGE_ENABLED=true \
  -e AZURE_CONNECTION_STRING="your-connection-string-here" \
  -e AZURE_CONTAINER_NAME=genfilesmcp \
  -e AZURE_SAS_EXPIRY_HOURS=24 \
  --name gen_files_mcp \
  genfilesmcp
```

### Option 3: Docker Compose

If you want to build the image yourself (you have the Dockerfile and local dependencies):

- Clone the repository

```shell
git clone https://github.com/Baronco/GenFilesMCP.git
cd GenFilesMCP
```

- Use the docker-compose.yml:

```yaml
services:
genfilesmcp:
  build:
  context: .
  dockerfile: Dockerfile
  container_name: genfilesmcp
  environment:
    - ENABLE_CREATE_KNOWLEDGE=false
    - OWUI_URL=http://open-webui:8080
    - PORT=8015
```

If you only want to use the image published on GitHub, modify the docker-compose.yml:

```yaml
services:
  genfilesmcp:
    image: ghcr.io/baronco/genfilesmcp:latest
    container_name: genfilesmcp
    environment:
      - ENABLE_CREATE_KNOWLEDGE=false
      - OWUI_URL=http://open-webui:8080
      - PORT=8015
```

Finally, run the Docker Compose setup:

```shell
docker compose up -d
```

## Configuration

### Environment Variables

The MCP server requires the following environment variables:

| Variable                     | Description                                   | Required | Default       | Example                              |
| ---------------------------- | --------------------------------------------- | -------- | ------------- | ------------------------------------ |
| `PORT`                       | Port where the MCP server will listen         | Yes      | `8015`        | `8015`                               |
| `AZURE_STORAGE_ENABLED`      | Enable Azure Blob Storage (must be `true`)    | Yes      | `true`        | `true`                               |
| `AZURE_USE_MANAGED_IDENTITY` | Use Azure Managed Identity for authentication | No       | `false`       | `false`                              |
| `AZURE_CONNECTION_STRING`    | Azure Storage connection string               | Yes\*    | -             | `DefaultEndpointsProtocol=https;...` |
| `AZURE_ACCOUNT_NAME`         | Azure Storage account name                    | Yes\*\*  | -             | `mystorageaccount`                   |
| `AZURE_CONTAINER_NAME`       | Blob container name                           | No       | `genfilesmcp` | `genfilesmcp`                        |
| `AZURE_SAS_EXPIRY_HOURS`     | SAS URL expiry time in hours                  | No       | `24`          | `24`                                 |

\* Required when `AZURE_USE_MANAGED_IDENTITY=false`  
\*\* Required when `AZURE_USE_MANAGED_IDENTITY=true` or for SAS URL generation

### Authentication Methods

**1. Connection String (Recommended for most deployments)**

```bash
PORT=8015
AZURE_STORAGE_ENABLED=true
AZURE_USE_MANAGED_IDENTITY=false
AZURE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=youraccount;AccountKey=yourkey;EndpointSuffix=core.windows.net"
AZURE_CONTAINER_NAME=genfilesmcp
AZURE_SAS_EXPIRY_HOURS=24
```

**2. Managed Identity (For Azure-hosted deployments only)**

```bash
PORT=8015
AZURE_STORAGE_ENABLED=true
AZURE_USE_MANAGED_IDENTITY=true
AZURE_ACCOUNT_NAME=youraccount
AZURE_CONTAINER_NAME=genfilesmcp
AZURE_SAS_EXPIRY_HOURS=24
```

### Docker Compose Example

```yaml
services:
  genfilesmcp:
    image: ghcr.io/baronco/genfilesmcp:latest
    container_name: genfilesmcp
    ports:
      - "8015:8015"
    environment:
      - PORT=8015
      - AZURE_STORAGE_ENABLED=true
      - AZURE_CONNECTION_STRING=your-connection-string-here
      - AZURE_CONTAINER_NAME=genfilesmcp
      - AZURE_SAS_EXPIRY_HOURS=24
```

## Usage

### Response Format

When a file is generated or reviewed, the server returns a JSON response with the following structure:

```json
{
  "file_path_download": "[Download filename.ext from Azure](https://...)",
  "sas_url": "https://account.blob.core.windows.net/container/file.ext?sv=...",
  "blob_name": "filename.ext",
  "container_name": "genfilesmcp",
  "expires_utc": "2025-12-11 14:30 UTC",
  "expiry_hours": 24
}
```

### Connecting to MCP Clients

This server implements the Model Context Protocol and can be connected to any MCP-compatible client (Claude Desktop, Open Web UI with MCP support, etc.).

**Server URL:** `http://localhost:8015/mcp` (or your configured host/port)

## Document Review Features

For document review functionality, you need to provide existing document files. The `full_context_docx` tool analyzes document structure, and `review_docx` adds comments to specified elements.

### Example Workflow

1. Upload a `.docx` file and note its `file_id`
2. Call `full_context_docx` to analyze the document structure
3. Call `review_docx` with specific comments for each element by index
4. Receive a reviewed document uploaded to Azure with SAS URL

## Setup for Azure Blob Storage

### Prerequisites

1. **Create an Azure Storage Account**

   - Go to [Azure Portal](https://portal.azure.com/)
   - Create a new Storage Account
   - Note your account name and connection string (or configure managed identity)

2. **Get Your Connection String**

   - In Azure Portal, navigate to your Storage Account
   - Go to "Access keys" under "Security + networking"
   - Copy the connection string

3. **Configure and Run**
   - Set the `AZURE_CONNECTION_STRING` environment variable
   - The blob container will be created automatically if it doesn't exist

### Security Considerations

- **SAS URLs are time-limited**: Configure `AZURE_SAS_EXPIRY_HOURS` based on your security requirements
- **Container permissions**: The blob container is created with private access; files are only accessible via SAS URLs
- **Connection string security**: Store your Azure connection string securely; use environment variables or secrets management
- **Managed Identity**: For Azure-hosted deployments, prefer managed identity over connection strings for enhanced security

## Usage Examples

### Example 1: Generating a DOCX file

<div style="text-align: center;">

![Generating DOCX Example](img/example2.png)

</div>

> **Example files**: You can find the prompt and generated result in the `example` folder: `History_of_Neural_Nets_Summary_69d1751b-577b-4329-beca-ac16db7acdbd.docx`

> This file was generated using the GenFiles MCP server and GPT-5 mini

### Example 2: Generating a XLSX file

<div style="text-align: center;">

![Generating XLSX Example 1](img/excel1.png)

</div>

Open the generated file in Excel:

<div style="text-align: center;">

![Generating XLSX Example 2](img/excel2.png)

</div>

### Example 3: Generating a PPTX file

In this example, it was used a MCP server to web research and GenFilesMCP to generate a PowerPoint presentation:

<div style="text-align: center;">

![Generating PPTX Example 1](img/powerpoint1.png)

</div>

Open the generated file in PowerPoint:

<div style="text-align: center;">

![Generating PPTX Example 2](img/powerpoint2.png)

</div>

> **Example files**: You can find the prompt and generated result in the `example` folder: `Cartagena_Temperature_Timeseries.xlsx`

### Example 4: Reviewing a DOCX file with comments

The review feature allows the agent to analyze uploaded documents and add structured comments for improvements.

<div style="text-align: center;">

![Review Example 1](img/reviewer1.png)

</div>

<div style="text-align: center;">

![Review Example 2](img/reviewer2.png)

</div>

<div style="text-align: center;">

![Review Example 3](img/reviewer3.png)

</div>

**Workflow:**

1. User uploads `History_of_Neural_Nets_Summary.docx` to provide file context
2. User requests a review with comments for corrections, grammar suggestions, and idea enhancements
3. Agent calls the `full_context_docx` MCP function to analyze the document structure
4. Agent calls the `review_docx` MCP function to add comments to specific elements
5. Reviewed document is uploaded to Azure Blob Storage with SAS URL provided

**Result:**

<div style="text-align: center;">

![DOCX Comments](img/docxcomments.png)

</div>

> **Example files**: Find the reviewed document in the `example` folder: `History_of_Neural_Nets_Summary_reviewed_a35adcc5-e338-47c6-a0b0-2c21602b0777.docx`

> Generated using the GenFiles MCP server

> The review functionality preserves the original formatting while adding structured comments

## Star History[![Star History Chart](https://api.star-history.com/svg?repos=Baronco/GenFilesMCP&type=date&legend=top-left)](https://www.star-history.com/#Baronco/GenFilesMCP&type=date&legend=top-left)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
