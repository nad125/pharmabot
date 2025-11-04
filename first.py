import parlant.sdk as p
import asyncio
import uuid
from datetime import datetime
import logging # Import standard logging
from dotenv import load_dotenv # Added to potentially load API keys

load_dotenv() # Load environment variables from .env file if it exists

# Configure standard Python logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- 1. Mock Data (Simulated Pharmacy Systems) ---
mock_inventory = {
    "Paracetamol 500mg Tablets": {"stock": 100, "requires_prescription": False},
    "Amoxicillin 250mg Capsules": {"stock": 50, "requires_prescription": True},
    "Ibuprofen 200mg Tablets": {"stock": 0, "requires_prescription": False},
    "Lisinopril 10mg Tablets": {"stock": 75, "requires_prescription": True},
}

mock_drug_info = {
    "Paracetamol 500mg Tablets": {
        "usage": "For mild to moderate pain relief and fever reduction.",
        "side_effects": "Generally well-tolerated. Rare side effects include allergic reactions.",
        "contraindications": "Severe liver disease.",
        "notes": "Follow dosage instructions carefully."
    },
    "Amoxicillin 250mg Capsules": {
        "usage": "Antibiotic for treating bacterial infections.",
        "side_effects": "Common: Nausea, rash, diarrhea. Seek medical attention for severe reactions.",
        "contraindications": "Known allergy to penicillin.",
        "notes": "Complete the full course as prescribed by your doctor."
    },
     "Lisinopril 10mg Tablets": {
        "usage": "Treats high blood pressure and heart failure.",
        "side_effects": "Common: Dizziness, cough, headache. Report persistent side effects to your doctor.",
        "contraindications": "History of angioedema, pregnancy.",
        "notes": "Take as directed by your healthcare provider."
    }
}

mock_orders = {} # Store simulated orders {order_id: details}
mock_prescriptions = {"RX12345": True, "RX67890": False} # Simple valid/invalid check

# --- 2. Tool Functions (Returning p.ToolResult) ---

@p.tool
async def check_stock(context: p.ToolContext, medication_name: str) -> p.ToolResult:
    """Checks the current stock level for a specific medication name."""
    logging.info(f"Tool 'check_stock' called with medication_name: {medication_name}")
    found_med = None
    stock_data = None
    for name, data in mock_inventory.items():
        # Case-insensitive matching
        if medication_name.lower() == name.lower():
             found_med = name
             stock_data = data
             break
        # Allow partial match as fallback, but prefer exact
        elif medication_name.lower() in name.lower() and not found_med:
            found_med = name
            stock_data = data # Keep checking for exact match

    if found_med and stock_data is not None:
        stock = stock_data["stock"]
        requires_rx = stock_data["requires_prescription"]
        rx_status = "Requires prescription." if requires_rx else "Does not require prescription."
        if stock > 0:
            logging.info(f"Stock check success for '{found_med}': {stock} units, Rx required: {requires_rx}")
            return p.ToolResult(
                data={"requires_prescription": requires_rx, "in_stock": True, "medication_name": found_med, "stock_count": stock},
                metadata={"feedback": f"'{found_med}' is in stock ({stock} units available). {rx_status}"},
            )
        else:
            logging.warning(f"Stock check failed for '{found_med}': Out of stock.")
            return p.ToolResult(
                data={"requires_prescription": requires_rx, "in_stock": False, "medication_name": found_med},
                metadata={"feedback": f"'{found_med}' is currently out of stock. {rx_status}", "is_error": True},
            )
    else:
        logging.warning(f"Stock check failed: Medication '{medication_name}' not found.")
        return p.ToolResult(
            data={"medication_found": False},
            metadata={"feedback": f"Sorry, I couldn't find '{medication_name}' in our inventory system.", "is_error": True},
        )


@p.tool
async def get_drug_info(context: p.ToolContext, medication_name: str) -> p.ToolResult:
    """Provides approved information (usage, side effects, contraindications) about a medication."""
    logging.info(f"Tool 'get_drug_info' called with medication_name: {medication_name}")
    found_med = None
    info_data = None
    for name, data in mock_drug_info.items():
         if medication_name.lower() == name.lower():
             found_med = name
             info_data = data
             break
         elif medication_name.lower() in name.lower() and not found_med:
            found_med = name
            info_data = data

    if found_med and info_data is not None:
        info_string = f"Information for '{found_med}':\n"
        info_string += f"- Usage: {info_data.get('usage', 'N/A')}\n"
        info_string += f"- Common Side Effects: {info_data.get('side_effects', 'N/A')}\n"
        info_string += f"- Contraindications: {info_data.get('contraindications', 'N/A')}\n"
        info_string += f"- Notes: {info_data.get('notes', 'N/A')}\n\n"
        info_string += "**Disclaimer:** This is not medical advice. Always consult your doctor or pharmacist for medical guidance."
        logging.info(f"Drug info found for '{found_med}'.")
        return p.ToolResult(data={"info_found": True}, metadata={"feedback": info_string})
    else:
        logging.warning(f"Drug info failed: Medication '{medication_name}' not found.")
        return p.ToolResult(
            data={"info_found": False},
            metadata={"feedback": f"Sorry, I don't have detailed information available for '{medication_name}'.", "is_error": True},
        )

@p.tool
async def verify_prescription(context: p.ToolContext, prescription_ref: str) -> p.ToolResult:
    """Checks if a given prescription reference is valid in the system."""
    logging.info(f"Tool 'verify_prescription' called with prescription_ref: {prescription_ref}")
    ref_upper = prescription_ref.upper()
    is_valid = mock_prescriptions.get(ref_upper, False)
    if is_valid:
        logging.info(f"Prescription '{ref_upper}' verified successfully.")
        return p.ToolResult(data={"verified": True}, metadata={"feedback": f"Prescription '{ref_upper}' is valid."})
    else:
        logging.warning(f"Prescription verification failed for '{ref_upper}'.")
        return p.ToolResult(
            data={"verified": False},
            metadata={"feedback": f"I couldn't verify prescription reference '{ref_upper}'. Please double-check the reference number.", "is_error": True},
        )

@p.tool
async def place_order(
    context: p.ToolContext,
    medication_name: str,
    quantity: int,
    prescription_ref: str | None = None
) -> p.ToolResult:
    """Places an order for a medication after checks. Requires quantity. Prescription ref needed if drug requires it."""
    logging.info(f"Tool 'place_order' called: med='{medication_name}', qty={quantity}, rx='{prescription_ref}'")
    found_med = None
    stock_data = None
    for name, data in mock_inventory.items():
         if medication_name.lower() == name.lower(): # Prioritize exact match
             found_med = name
             stock_data = data
             break
         elif medication_name.lower() in name.lower() and not found_med:
            found_med = name
            stock_data = data

    if not found_med or stock_data is None:
        logging.error(f"Order placement failed: Medication '{medication_name}' not found.")
        return p.ToolResult(data={"order_placed": False, "reason": "Medication not found"}, metadata={"feedback": f"Cannot place order. Medication '{medication_name}' not found.", "is_error": True})

    try:
        quantity_int = int(quantity)
        if quantity_int <= 0:
            raise ValueError("Quantity must be positive")
    except (ValueError, TypeError):
         logging.error(f"Order placement failed for '{found_med}': Invalid quantity '{quantity}'.")
         return p.ToolResult(data={"order_placed": False, "reason": "Invalid quantity"}, metadata={"feedback": f"Cannot place order. Please provide a valid positive number for the quantity.", "is_error": True})

    if stock_data["stock"] < quantity_int:
        logging.error(f"Order placement failed for '{found_med}': Insufficient stock (needed {quantity_int}, have {stock_data['stock']}).")
        return p.ToolResult(data={"order_placed": False, "reason": "Insufficient stock"}, metadata={"feedback": f"Cannot place order. Insufficient stock for '{found_med}'. Available: {stock_data['stock']}.", "is_error": True})

    prescription_ref_upper = prescription_ref.upper() if prescription_ref else None

    if stock_data["requires_prescription"]:
        if not prescription_ref_upper:
            logging.error(f"Order placement failed for '{found_med}': Missing required prescription ref.")
            return p.ToolResult(data={"order_placed": False, "reason": "Missing prescription"}, metadata={"feedback": f"Cannot place order. '{found_med}' requires a prescription reference, but none was provided.", "is_error": True})
        is_valid_rx = mock_prescriptions.get(prescription_ref_upper, False)
        if not is_valid_rx:
             logging.error(f"Order placement failed for '{found_med}': Prescription '{prescription_ref_upper}' failed verification.")
             return p.ToolResult(data={"order_placed": False, "reason": "Prescription invalid"}, metadata={"feedback": f"Cannot place order. Prescription reference '{prescription_ref_upper}' could not be verified.", "is_error": True})
    elif prescription_ref_upper:
         logging.warning(f"Note: Prescription '{prescription_ref_upper}' provided for non-prescription item '{found_med}'.")

    # Simulate placing order
    order_id = str(uuid.uuid4())[:8].upper()
    mock_orders[order_id] = {
        "medication": found_med,
        "quantity": quantity_int,
        "prescription_ref": prescription_ref_upper,
        "status": "Processing",
        "timestamp": datetime.now().isoformat()
    }
    mock_inventory[found_med]["stock"] -= quantity_int
    logging.info(f"Order placed successfully for {quantity_int}x '{found_med}'. Order ID: {order_id}. New stock: {mock_inventory[found_med]['stock']}")

    return p.ToolResult(
        data={"order_placed": True, "order_id": order_id},
        metadata={"feedback": f"Order placed successfully! Your Order ID is {order_id}. Current status: Processing."},
    )


@p.tool
async def check_order_status(context: p.ToolContext, order_id: str) -> p.ToolResult:
    """Checks the status of an existing order using its Order ID."""
    logging.info(f"Tool 'check_order_status' called with order_id: {order_id}")
    order_id_upper = order_id.upper()
    order = mock_orders.get(order_id_upper)
    if order:
        logging.info(f"Order status found for '{order_id_upper}': {order['status']}")
        return p.ToolResult(data={"status_found": True}, metadata={"feedback": f"Order {order_id_upper} Status: {order['status']}. Placed for {order['quantity']}x '{order['medication']}'."})
    else:
        logging.warning(f"Order status check failed: Order ID '{order_id_upper}' not found.")
        return p.ToolResult(
            data={"status_found": False},
            metadata={"feedback": f"Sorry, I could not find an order with ID '{order_id_upper}'. Please check the ID.", "is_error": True},
        )

# --- 3. Journey Creation Functions ---

async def create_new_order_journey(agent: p.Agent):
    """Creates the journey for placing a new medication order."""
    journey = await agent.create_journey(
        title="Place New Medication Order",
        description="Guides the customer through placing a new order for medication.",
        conditions=[
            "customer wants to order a medication",
            "buy medicine",
            "need to purchase a drug"
        ]
    )
    # Define states and transitions using the healthcare.py pattern
    t0 = await journey.initial_state.transition_to(
        chat_state="Ask which medication the customer needs."
    )
    t1 = await t0.target.transition_to(
        tool_state=check_stock # Execute check_stock tool
    )
    # State after stock check
    state_after_stock_check = t1.target

    # Path if Rx is needed
    t2_rx = await state_after_stock_check.transition_to(
        chat_state="Ask for the prescription reference number as the medication requires it.",
        condition="The tool 'check_stock' result data indicates 'requires_prescription' is true AND 'in_stock' is true" # Condition based on tool output data
    )
    t3_verify = await t2_rx.target.transition_to(
        tool_state=verify_prescription # Execute verify_prescription tool
    )
    state_after_verify = t3_verify.target # State after prescription verification attempt

    t4_qty_rx = await state_after_verify.transition_to(
        chat_state="Ask how many units the customer would like to order (e.g., number of tablets/capsules).",
        condition="The tool 'verify_prescription' result data indicates 'verified' is true"
    )
    state_ask_qty_rx = t4_qty_rx.target # State asking for quantity (Rx path)

    # Path if Rx is NOT needed (and in stock)
    t4_qty_no_rx = await state_after_stock_check.transition_to(
        chat_state="Ask how many units the customer would like to order (e.g., number of tablets/capsules).",
        condition="The tool 'check_stock' result data indicates 'requires_prescription' is false AND 'in_stock' is true"
    )
    state_ask_qty_no_rx = t4_qty_no_rx.target # State asking for quantity (No Rx path)

    # --- Refactored Part ---
    # The SDK no longer exposes `journey.create_state` publicly. Create the
    # shared `place_order` state by creating it from one of the quantity states
    # (this will return the created state), then point the other quantity path
    # at that same state using `transition_to(state=...)`.
    t_place_from_rx = await state_ask_qty_rx.transition_to(
        tool_state=place_order,
        condition="User provides a valid quantity"
    )
    state_place_order = t_place_from_rx.target

    # Reuse the same place_order state for the no-Rx path
    await state_ask_qty_no_rx.transition_to(
        state=state_place_order,
        condition="User provides a valid quantity"
    )
    # --- End of Refactored Part ---

    # Transitions *from* the place_order state (state_place_order is now the correct object)
    t6_confirm = await state_place_order.transition_to(
         chat_state="Confirm the order placement and provide the Order ID.",
         condition="The tool 'place_order' result data indicates 'order_placed' is true"
    )
    # End journey after confirmation
    await t6_confirm.target.transition_to(state=p.END_JOURNEY)


    # --- Error Handling Transitions ---
    # Out of stock error (from state_after_stock_check)
    t_error_stock = await state_after_stock_check.transition_to(
        chat_state="Inform the customer the medication is out of stock and ask if they want alternatives discussed with a pharmacist.",
        condition="The tool 'check_stock' result data indicates 'in_stock' is false"
    )
    await t_error_stock.target.transition_to(state=p.END_JOURNEY) # End after informing

     # Medication not found error (from state_after_stock_check)
    t_error_notfound = await state_after_stock_check.transition_to(
        chat_state="Inform the customer the medication was not found in the system and ask them to verify the spelling or try another name.",
        condition="The tool 'check_stock' result data indicates 'medication_found' is false"
    )
    await t_error_notfound.target.transition_to(state=p.END_JOURNEY) # End after informing

    # Invalid prescription error (from state_after_verify)
    t_error_rx = await state_after_verify.transition_to(
        chat_state="Inform the customer the prescription reference could not be verified and ask them to check or contact support.",
        condition="The tool 'verify_prescription' result data indicates 'verified' is false"
    )
    await t_error_rx.target.transition_to(state=p.END_JOURNEY) # End after informing

    # Order placement error (from state_place_order)
    t_error_order = await state_place_order.transition_to(
        chat_state="Inform the customer the order could not be placed due to an issue (e.g., stock changed, invalid quantity) and suggest trying again or contacting support. Provide reason if available from tool feedback.",
        condition="The tool 'place_order' result data indicates 'order_placed' is false"
    )
    await t_error_order.target.transition_to(state=p.END_JOURNEY) # End after informing

    # Add journey-specific guidelines if needed (like in healthcare example)
    # e.g., await journey.create_guideline(...)

    return journey

async def create_drug_info_journey(agent: p.Agent):
    """Creates the journey for providing drug information."""
    journey = await agent.create_journey(
        title="Get Medication Information",
        description="Provides approved information about a specific medication.",
        conditions=[
            "customer wants information about a drug",
            "tell me about medication",
            "side effects of",
            "how to use medicine"
        ]
    )
    t0 = await journey.initial_state.transition_to(
        chat_state="Ask for the name of the medication the customer wants information about."
    )
    t1 = await t0.target.transition_to(
        tool_state=get_drug_info # Execute get_drug_info tool
    )
    t2_success = await t1.target.transition_to(
        chat_state="Ask if the customer has any other questions or needs further assistance.",
        condition="The tool 'get_drug_info' result data indicates 'info_found' is true"
    )
    await t2_success.target.transition_to(state=p.END_JOURNEY) # End after asking

    t2_fail = await t1.target.transition_to(
        chat_state="Apologize for not having information and ask if they need help with something else.",
        condition="The tool 'get_drug_info' result data indicates 'info_found' is false"
    )
    await t2_fail.target.transition_to(state=p.END_JOURNEY) # End after apologizing

    return journey

async def create_order_status_journey(agent: p.Agent):
    """Creates the journey for checking order status."""
    journey = await agent.create_journey(
        title="Check Order Status",
        description="Checks the status of an existing medication order.",
        conditions=[
            "customer wants to check order status",
            "where is my order",
            "status of order"
        ]
    )
    t0 = await journey.initial_state.transition_to(
        chat_state="Ask for the Order ID."
    )
    t1 = await t0.target.transition_to(
        tool_state=check_order_status # Execute check_order_status tool
    )
    t2_success = await t1.target.transition_to(
        chat_state="Provide the order status and ask if further help is needed.",
        condition="The tool 'check_order_status' result data indicates 'status_found' is true"
    )
    await t2_success.target.transition_to(state=p.END_JOURNEY)

    t2_fail = await t1.target.transition_to(
        chat_state="Inform the customer the Order ID wasn't found and ask them to verify or contact support.",
        condition="The tool 'check_order_status' result data indicates 'status_found' is false"
    )
    await t2_fail.target.transition_to(state=p.END_JOURNEY)

    return journey

async def add_domain_glossary(agent: p.Agent):
    """Adds domain-specific terms to the agent's glossary."""
    logging.info("Adding glossary terms...")
    await agent.create_term(
        name="Prescription",
        description="An instruction written by a medical practitioner that authorizes a patient to be provided a medicine or treatment."
    )
    await agent.create_term(
        name="Refill",
        description="A subsequent dispensing of a medication previously authorized by a prescription."
    )
    await agent.create_term(
        name="Medical Advice",
        description="Recommendations regarding diagnosis, treatment, or prevention of medical conditions. You are strictly prohibited from providing medical advice. Always refer the user to a qualified healthcare professional."
    )
    await agent.create_term(
         name="Side Effects",
         description="Unintended secondary effects which a drug or medical treatment has on the body. Only provide information listed in the approved drug info."
    )
    await agent.create_term(
         name="Contraindications",
         description="Specific situations in which a drug should not be used because it may be harmful to the person. Only provide information listed in the approved drug info."
    )
    await agent.create_term(
         name="Pharmacist",
         description="A licensed healthcare professional specializing in medication dispensing and counseling. Human pharmacists are available for complex questions."
    )
    await agent.create_term(
         name="Pharmacy Phone Number",
         description="Our pharmacy phone number is +1-800-PHARMA-1."
    )
    await agent.create_term(
         name="Pharmacy Hours",
         description="We are open Monday to Friday, 9 AM to 7 PM, and Saturday 10 AM to 4 PM. Closed Sundays."
    )


# --- 4. Main Application Logic ---

async def main():
    """Initializes and runs the Parlant server and agent."""
    logging.info("Starting PharmaPal agent setup...")
    # Example: configure OpenAI using environment variable loaded by dotenv
    # You might need to install openai package: pip install openai
    # p.configure_openai() # Reads OPENAI_API_KEY from env if available

    async with p.Server() as server:
        logging.info(f"Parlant server started on port {server.port}")
        agent = await server.create_agent(
            name="PharmaPal",
            description="""You are PharmaPal, a helpful and compliant pharmacy sales assistant AI.
Your primary functions are assisting customers with medication orders, checking stock/prescription needs, providing basic approved drug info, checking order status, and answering simple refill questions.
You are professional, empathetic, accurate, and patient. Compliance and safety are critical.

**CRITICAL RULES:**
* **NO MEDICAL ADVICE:** Never provide medical advice, diagnoses, dosage recommendations (unless repeating verified prescription details for an order), or treatment suggestions. If asked, politely refuse, state your limitation as an AI, and direct the user to consult a qualified healthcare professional (doctor or pharmacist).
* **USE TOOLS ONLY:** Base drug information (usage, side effects, contraindications) strictly on the results from the `get_drug_info` tool. Do not infer or add external knowledge.
* **PRIVACY:** Adhere to privacy guidelines. Only ask for information essential to the task (e.g., medication name, quantity, order ID, prescription ref). Do not ask for unnecessary health details.
* **DRUG INTERACTIONS/SEVERE SYMPTOMS:** Do not attempt to analyze drug interactions or severe symptoms. For interactions, refer to a pharmacist/doctor. For severe symptoms, express empathy, stop the process, and strongly advise seeking immediate medical attention or contacting emergency services.
* **PRESCRIPTIONS:** If a drug requires a prescription per the `check_stock` tool, always verify it using the `verify_prescription` tool before proceeding with an order.
* **HUMAN HANDOFF:** If requested, or if the situation is complex, sensitive, requires professional judgment, or you are unable to proceed, offer to connect the user to a human pharmacist.
""",
            # model="gpt-4o" # Specify model if needed
        )
        logging.info(f"Agent '{agent.name}' created.")

        # Tools decorated with @p.tool are automatically discovered.
        logging.info("Tools discovered automatically by Parlant.")

        # Add Glossary
        await add_domain_glossary(agent)

        # Create Journeys
        logging.info("Creating journeys...")
        order_journey = await create_new_order_journey(agent)
        info_journey = await create_drug_info_journey(agent)
        status_journey = await create_order_status_journey(agent)
        # Add Refill Journey creation call here if implemented
        logging.info("Journeys created.")

        # --- Disambiguation for Ambiguous Requests ---
        # Example: User asks "Can you help with my Lisinopril order?" (New order or status check?)
        order_inquiry = await agent.create_observation(
             "The customer mentions a specific medication and the word 'order', but it's unclear if they want to place a new one or check an existing one."
        )
        # Link the observation to relevant journeys
        await order_inquiry.disambiguate([order_journey, status_journey])


        # --- Global Guidelines ---
        logging.info("Adding global guidelines...")
        # Medical Advice Guideline (High Priority)
        await agent.create_guideline(
            condition="Customer asks for medical advice, diagnosis, dosage recommendations (not related to a specific order confirmation), or treatment suggestions",
            action="CRITICAL: Immediately and politely refuse. State you are an AI assistant and legally cannot provide medical advice. Recommend they consult their doctor or pharmacist using the Pharmacy Phone Number.",
            metadata={"priority": 10}
        )
        # Drug Interaction Guideline
        await agent.create_guideline(
            condition="Customer asks about specific drug interactions",
            action="Politely refuse. State that drug interactions are complex and potentially dangerous, and must be discussed with a qualified pharmacist or doctor who knows their full medical history. Offer Pharmacy Phone Number.",
            metadata={"priority": 9}
        )
        # Severe Symptoms Guideline (Highest Priority)
        await agent.create_guideline(
            condition="Customer describes severe symptoms or distress (e.g., 'severe pain', 'trouble breathing', 'allergic reaction', 'feeling faint')",
            action="Express empathy briefly. STOP the current process. Strongly advise seeking immediate medical attention (e.g., 'For symptoms like that, please contact emergency services or your doctor right away.') Offer emergency contact info if configured.",
            metadata={"priority": 11}
        )
        # Off-Topic Guideline
        await agent.create_guideline(
            condition="Customer asks a question unrelated to pharmacy services, ordering, medication info, or operating hours/contact",
            action="Politely redirect the conversation back to pharmacy-related topics. State your purpose (e.g., 'I can help with medication orders, provide basic drug information, check order status, and give our hours. How can I assist you with those today?')."
        )
        # Missing Prescription Guideline (specific to order context, but can be global)
        await agent.create_guideline(
            condition="Customer asks to order a medication identified by 'check_stock' as requiring a prescription, but does not provide a reference",
            action="Inform them the medication requires a valid prescription reference number to proceed with an order. Ask if they have one.",
            # This might be better handled within the journey, but can be a global fallback
        )
        # Frustration/Confusion Guideline
        await agent.create_guideline(
            condition="Customer expresses significant frustration, confusion, or repeats the same failed request",
            action="Respond with empathy and patience. Offer to clarify or try explaining differently. Ask if they would prefer to speak with a human pharmacist via the Pharmacy Phone Number."
        )
        # Explicit Human Handoff Request Guideline
        await agent.create_guideline(
            condition="Customer explicitly asks to speak to a human, agent, or pharmacist",
            action="Acknowledge the request. Provide the Pharmacy Phone Number and Pharmacy Hours. State that a human pharmacist can provide further assistance. [System Note: Log Handoff Request]",
            metadata={"priority": 8}
        )
        # Implicit Handoff (Complex/Sensitive/Stuck) Guideline
        await agent.create_guideline(
            condition="Conversation involves complex issues beyond tool capabilities OR agent is stuck in a loop OR detects high user distress not covered by severe symptoms guideline",
            action="Politely state the limitation. Offer to connect them with a human pharmacist. Provide Pharmacy Phone Number and Pharmacy Hours. [System Note: Log Implicit Handoff Trigger]",
            metadata={"priority": 7} # Lower than explicit request
        )
        logging.info("Guidelines added.")

        print("\n--- PharmaPal Sales Bot Ready! ---")
        print(f"Parlant UI likely available at: http://localhost:{server.port}")
        print("Press Ctrl+C to stop.")

    # The SDK's Server does not expose `serve_forever()`; use a simple
    # event wait to keep the context alive until interrupted by the user.
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        logging.exception("Unhandled exception occurred during main execution.")