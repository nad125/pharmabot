# pharmabot
Here is a professional `README.md` file for the pharmacy agent code you provided.

-----

# PharmaPal 💊: AI Pharmacy Voice Agent

PharmaPal is a sophisticated, compliant AI voice assistant built using the `parlant.sdk`. It's designed to simulate a real pharmacy's customer service, handling tasks like placing orders, checking stock, providing approved drug information, and checking order status in a structured, safe, and conversational manner.

This agent is built with a compliance-first mindset, featuring critical safety guidelines to prevent providing medical advice and to handle sensitive situations appropriately.

## Features

  * **Multi-Turn Journeys:** Guides users through complex, multi-step tasks like placing a new order.
  * **Stock & Prescription Checks:** Verifies medication availability and prescription requirements in real-time from a mock database.
  * **Prescription Verification:** Validates mock prescription reference numbers before processing an order.
  * **Approved Drug Information:** Answers user questions about medication usage, side effects, and contraindications using a sandboxed knowledge base.
  * **Order Status:** Allows users to retrieve the status of a previously placed order using their order ID.
  * **Compliance-First Design:** Includes critical, high-priority guidelines to prevent the AI from giving medical advice and to manage human handoff requests.

## How It Works (Agent Architecture)

This agent is built using several key concepts from the `parlant.sdk`:

  * **Tools (`@p.tool`):** The agent's core capabilities (e.g., `check_stock`, `place_order`) are defined as asynchronous Python functions. The agent decides which tool to call based on the user's request.
  * **Journeys:** These are pre-defined conversational flows for multi-step tasks. This agent uses three main journeys:
    1.  `create_new_order_journey`
    2.  `create_drug_info_journey`
    3.  `create_order_status_journey`
  * **Guidelines:** These are global, high-priority rules that govern the agent's behavior at all times. This agent includes critical guidelines to **prevent providing medical advice**, handle **requests for a human pharmacist**, and manage discussions of **severe symptoms**.
  * **Glossary:** Provides the AI with domain-specific knowledge (e.g., definitions for "Pharmacist," "Refill," "Contraindications") to improve its understanding and response accuracy.
  * **Mock Backend:** All data (inventory, orders, prescriptions) is simulated in mock Python dictionaries at the top of the script. No external database is required to run this demo.

## Setup & Installation

1.  **Clone this repository** (or save the Python file, assuming you name it `main.py`).

2.  **Create a Virtual Environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    You will need to install the `parlant.sdk` and `python-dotenv`.

    Create a `requirements.txt` file with the following content:

    ```txt
    parlant.sdk
    python-dotenv
    # openai  # Uncomment if you plan to configure p.configure_openai()
    ```

    Then, install the requirements:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables (Optional):**
    This script uses `python-dotenv` to load environment variables. If your `parlant.sdk` is configured to use an LLM provider that requires an API key (like OpenAI), create a `.env` file in the same directory:

    ```
    OPENAI_API_KEY="sk-..."
    ```

## Running the Agent

To run the PharmaPal agent, simply execute the main Python script:

```bash
python main.py
```

The server will start, and you will see logging output in your terminal. The agent "PharmaPal" will be active and ready to accept connections.

```
$ python main.py
INFO:asyncio:Starting PharmaPal agent setup...
INFO:asyncio:Parlant server started on port 8000
INFO:asyncio:Agent 'PharmaPal' created.
INFO:asyncio:Tools discovered automatically by Parlant.
INFO:asyncio:Adding glossary terms...
INFO:asyncio:Creating journeys...
INFO:asyncio:Journeys created.
INFO:asyncio:Adding global guidelines...
INFO:asyncio:Guidelines added.

--- PharmaPal Sales Bot Ready! ---
Parlant UI likely available at: http://localhost:8000
Press Ctrl+C to stop.
```

You can now interact with your agent using the Parlant UI, which is typically available at **`http://localhost:8000`**.

## Agent Capabilities

This agent's behavior is defined by the following tools and guidelines:

### Tools

  * `check_stock(medication_name)`: Checks if a medication is in stock and if it requires a prescription.
  * `get_drug_info(medication_name)`: Provides official usage, side effects, and notes for a drug.
  * `verify_prescription(prescription_ref)`: Validates a prescription reference number.
  * `place_order(medication_name, quantity, prescription_ref=None)`: Places an order after performing all necessary stock and prescription checks.
  * `check_order_status(order_id)`: Retrieves the status of an existing order by ID.

### Critical Guidelines

  * **No Medical Advice:** The agent is strictly prohibited from giving medical advice, diagnoses, or treatment suggestions.
  * **Emergency Handoff:** If a user mentions severe symptoms (e.g., "trouble breathing"), the agent will stop its current task and advise seeking immediate medical attention.
  * **Human Handoff:** If the user asks to speak to a human or pharmacist, the agent will provide the pharmacy's contact information and operating hours.
