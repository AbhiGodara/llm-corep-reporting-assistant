from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from schemas.own_funds_schema import OwnFundsReport
import dotenv
import os
dotenv.load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

def generate_report(context, scenario):
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="openai/gpt-oss-120b",
        temperature=0
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
            "You are a regulatory reporting assistant for UK COREP Own Funds. "
            "You must extract numeric values explicitly stated in the scenario. "
            "If required numeric values are missing or unclear, you MUST return an error "
            "instead of guessing or defaulting to zero."),

        ("human",
            """
                Regulatory text:
                {context}

                Scenario:
                {scenario}

                Rules:
                - Extract CET1, AT1, and Tier 2 ONLY if explicitly stated as numbers.
                - Do NOT assume or default values.
                - If any required value is missing, return JSON with error message:
                {{ "error": "Missing required field: <missing required field name>" }}

                Otherwise, return ONLY valid JSON matching this schema:
                {schema}
            """)

    ])

    response = llm.invoke(
        prompt.format_messages(
            context=context,
            scenario=scenario,
            schema=OwnFundsReport.schema_json()
        )
    )

    return response.content
