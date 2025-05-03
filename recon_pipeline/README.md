# Recon Briefing Pipeline (Mirascope SDK V1 Demo)

## 1. Project Overview

This project demonstrates a multi-agent pipeline built using the Mirascope Python SDK (v1.x) without relying on the Mirascope CLI. It simulates an intelligence gathering operation using an army metaphor:

*   **Scout Agents:** Fetch raw data (news headlines) from various sources.
*   **Analyst Agent:** Processes the raw data, performing deduplication, clustering, and summarization using LLM calls defined via Mirascope decorators.
*   **Commander Agent:** Synthesizes the processed information, generates a final briefing email (including an infographic), and handles dispatch (currently prints to console or sends via SMTP if configured).

The orchestration is handled purely in Python using `asyncio`, showcasing how to build complex agent workflows programmatically with Mirascope's decorator-based API.

## 2. Components

*   **`requirements.txt`**: Lists all necessary Python package dependencies (`mirascope`, `feedparser`, `httpx`, `matplotlib`, `pydantic`, `python-dotenv`).
*   **`scout.py`**: Contains the `fetch_headlines` async function using `httpx` and `feedparser` to retrieve news headlines from RSS feeds. Defines the `Headline` Pydantic model.
*   **`analyst.py`**: Defines the `summarize_headlines` async function using the `@openai.call` decorator to interact with an LLM (e.g., GPT-4o Mini) for processing and summarizing headlines based on the provided docstring prompt.
*   **`commander.py`**: Defines the `compose_email` async function using `@openai.call` and `response_model=EmailContent` to generate structured email output (subject, body, chart data). Also includes Python functions `generate_chart` (using `matplotlib`) and `send_email` (using `smtplib` or printing to console).
*   **`main.py`**: The main orchestration script using `asyncio`. It defines the news sources, calls the scout, analyst, and commander functions in sequence, and manages the data flow between them.
*   **`.env` (Manual Creation Required)**: Used to store sensitive credentials like `OPENAI_API_KEY` and optional SMTP settings. Loaded by the scripts using `python-dotenv`.

## 3. Features

*   **Mirascope SDK V1 Focus**: Demonstrates building agents using the core Mirascope library and decorators, without the CLI.
*   **Pure Python Orchestration**: Uses standard `asyncio` for managing asynchronous tasks and data flow between agents.
*   **Decorator-Based LLM Calls**: Leverages Mirascope's `@openai.call` for clean integration with LLMs, including prompt templating via docstrings and structured output parsing via `response_model`.
*   **Structured Data Handling**: Uses Pydantic models (`Headline`, `EmailContent`) for clear data definition and validation.
*   **Asynchronous Operations**: Efficiently handles network I/O for fetching headlines and making LLM calls using `async`/`await`.
*   **Modular Design**: Each agent's logic is contained within its respective script, making it easier to understand, test, and modify.
*   **Extensible**: Designed to be easily extended with new data sources, agent types, or output channels.

## 4. Prerequisites

*   **Python**: Version 3.10 or higher recommended.
*   **OpenAI API Key**: You must have an API key from OpenAI. Set it as an environment variable named `OPENAI_API_KEY`.
*   **Environment Variable File (`.env`)**: A `.env` file in the project root (`recon_pipeline/`) to store the `OPENAI_API_KEY` (and optionally SMTP details).
*   **Network Access**: Internet connectivity is required to fetch RSS feeds and contact the OpenAI API.
*   **`pip` and `venv`**: Standard Python package management tools.

## 5. Installation

1.  **Clone the Repository** (if applicable):
    ```bash
    # git clone <repository-url>
    cd recon_pipeline
    ```
    (If you don't have a repo, just ensure you are in the `recon_pipeline` directory containing the scripts).

2.  **Create and Activate Virtual Environment**:
    ```bash
    python3 -m venv venv
    # On macOS/Linux:
    source venv/bin/activate
    # Or if 'source' causes issues:
    # . venv/bin/activate

    # On Windows (Git Bash):
    # source venv/Scripts/activate
    # On Windows (Command Prompt):
    # venv\Scripts\activate.bat
    # On Windows (PowerShell):
    # venv\Scripts\Activate.ps1
    ```
    *(Your prompt should now start with `(venv)`)*

3.  **Install Dependencies**:
    ```bash
    python -m pip install -r requirements.txt
    ```

4.  **Create and Populate `.env` File**:
    Manually create a file named `.env` in the `recon_pipeline` directory. Add your `OPENAI_API_KEY` and the `MIRASCOPE_DOCSTRING_PROMPT_TEMPLATE` flag:
    ```env
    OPENAI_API_KEY="your-openai-api-key-here"
    MIRASCOPE_DOCSTRING_PROMPT_TEMPLATE=ENABLED

    # Optional: SMTP Credentials for Commander
    # SMTP_SERVER="smtp.example.com"
    # SMTP_PORT=587
    # SMTP_USER="your_email@example.com"
    # SMTP_PASSWORD="your_email_password"
    # RECIPIENT_EMAILS="recipient1@example.com,recipient2@example.com"
    ```
    Replace the placeholder API key. Uncomment and fill in SMTP details if desired.

## 6. Configuration

*   **News Sources**: Modify the `NEWS_SOURCES` dictionary in `main.py` to change or add RSS feed URLs.
*   **LLM Models**: Change the `model="gpt-4o-mini"` argument in the `@openai.call` decorators in `analyst.py` and `commander.py` to use different compatible OpenAI models.
*   **Prompts**: Edit the docstrings within the decorated functions (`summarize_headlines`, `compose_email`) in `analyst.py` and `commander.py` to adjust the LLM's instructions.
*   **API Keys & SMTP**: Configure the `OPENAI_API_KEY` and optional SMTP settings in the `.env` file.
*   **Headline Fetch Limit**: Adjust the `limit` parameter in the `fetch_headlines` calls within `main.py` (currently defaults to 5 in the `scout.py` function signature if not overridden).

## 7. Usage

Ensure your virtual environment is activated (`source venv/bin/activate` or `. venv/bin/activate`) before running commands.

*   **Run the Full Pipeline**:
    ```bash
    python main.py
    ```
    Monitor the console logs for progress and the final email output (either printed to console or sent via SMTP).

*   **Run Individual Agents (for testing/debugging)**:
    ```bash
    # Test Scout fetching (uses BBC News feed by default)
    python scout.py

    # Test Analyst summarization (uses hardcoded sample headlines)
    python analyst.py

    # Test Commander email composition (uses hardcoded sample summaries)
    python commander.py
    ```

## 8. Project Structure

```
recon_pipeline/
├── .env                 # (Needs manual creation) Stores API keys, SMTP config
├── venv/                # Python virtual environment directory
├── main.py              # Main orchestration script
├── scout.py             # Headline fetching logic
├── analyst.py           # Headline summarization logic (LLM call)
├── commander.py         # Email composition (LLM call), chart generation, sending
├── requirements.txt     # Project dependencies
└── recon_chart.png      # Temporary chart image (generated and deleted during run)
```

## 9. Extending the Pipeline

*   **Add More Scouts**: Create functions to fetch data from different sources (e.g., APIs like NewsAPI, Twitter/X, web scraping) and integrate them into `main.py`.
*   **Use Different LLMs**: Adapt the `@*.call` decorators to use other providers supported by Mirascope (e.g., `@anthropic.call`, `@google.call` after installing `mirascope[anthropic]` or `mirascope[google]` and setting appropriate keys).
*   **Enhance Analysis**: Implement more sophisticated clustering (e.g., using embeddings) or analysis (e.g., sentiment analysis) in the Analyst phase.
*   **Add Dispatch Channels**: Modify the Commander to send briefings via other methods (e.g., Slack, Discord, saving to a file).
*   **Improve Error Handling**: Add more robust error handling and retry logic (e.g., using `tenacity` with Mirascope calls).
*   **Configuration Management**: Move configuration like `NEWS_SOURCES` out of `main.py` into a separate config file (e.g., YAML or JSON).

## 10. Contributing

Contributions are welcome! Please follow standard GitHub practices:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  Make your changes and commit them (`git commit -am 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Create a new Pull Request against the `main` branch.

## 11. License

This project is licensed under the MIT License. See the LICENSE file for details (if one exists in the repository).
