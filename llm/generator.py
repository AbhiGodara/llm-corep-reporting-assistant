import os
import json
import re
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from core.schemas import COREPReport, COREPField
import dotenv

dotenv.load_dotenv()

class ReportGenerator:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.3-70b-versatile",
            temperature=0.1
        )
        
    def extract_amounts_from_text(self, text: str) -> Dict[str, float]:
        """
        Extract financial amounts from text using regex.
        Helps the LLM by pre-extracting numbers.
        """
        amounts = {}
        
        # Patterns for different capital types
        patterns = {
            'cet1': r'(?:CET1|Common Equity Tier 1|common equity).*?(\d[,\d]*(?:\.\d+)?)\s*(?:million|m|M|£|€|EUR|GBP|USD)',
            'at1': r'(?:AT1|Additional Tier 1|additional tier).*?(\d[,\d]*(?:\.\d+)?)\s*(?:million|m|M|£|€|EUR|GBP|USD)',
            'tier2': r'(?:Tier 2|tier two).*?(\d[,\d]*(?:\.\d+)?)\s*(?:million|m|M|£|€|EUR|GBP|USD)',
            'total': r'(?:Total|total own funds|total capital).*?(\d[,\d]*(?:\.\d+)?)\s*(?:million|m|M|£|€|EUR|GBP|USD)',
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take the last match (most specific)
                amount_str = matches[-1].replace(',', '')
                try:
                    amount = float(amount_str)
                    amounts[key] = amount
                except:
                    pass
        
        return amounts
    
    def generate_report(self, context: str, scenario: str) -> Dict[str, Any]:
        """
        Generate COREP report from scenario and regulatory context.
        Returns dict with either report or error.
        """
        
        # Pre-extract amounts to help LLM
        extracted_amounts = self.extract_amounts_from_text(scenario)
        amounts_str = json.dumps(extracted_amounts, indent=2)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a COREP regulatory reporting assistant for UK banks.
            Extract capital values from the scenario and map to COREP Own Funds template fields.
            
            COREP FIELDS:
            - OF_010: Common Equity Tier 1 (CET1) capital
            - OF_020: Additional Tier 1 (AT1) capital  
            - OF_030: Tier 2 capital
            - OF_040: Total Own Funds (sum of OF_010 + OF_020 + OF_030)
            
            RULES:
            1. Extract ONLY values explicitly stated in the scenario.
            2. If a value is calculated/implied but not stated, set it to null.
            3. If CET1, AT1, or Tier 2 are stated but Total is not, calculate Total.
            4. All values must be non-negative.
            5. Values are in millions (e.g., "150 million" = 150).
            
            I found these amounts in the text: {amounts_found}
            """),
            
            ("human", """REGULATORY CONTEXT:
            {context}
            
            REPORTING SCENARIO:
            {scenario}
            
            Extract the values and return ONLY JSON matching this exact format:
            {{
                "template": "C 01.00",
                "fields": [
                    {{
                        "field_code": "OF_010",
                        "description": "Common Equity Tier 1 capital",
                        "value": <number or null>,
                        "confidence": <0.0 to 1.0>,
                        "justification": "<why you extracted this value>",
                        "source_rule": "<regulatory rule from context>"
                    }},
                    ... repeat for OF_020, OF_030, OF_040
                ]
            }}
            
            Return ONLY the JSON, no other text.""")
        ])
        
        try:
            response = self.llm.invoke(
                prompt.format_messages(
                    context=context,
                    scenario=scenario,
                    amounts_found=amounts_str
                )
            )
            
            # Clean the response
            content = response.content.strip()
            
            # Extract JSON if wrapped in markdown or other text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()
            
            # Parse and validate
            data = json.loads(content)
            
            # Validate required structure
            if "fields" not in data:
                return {"error": "Invalid response: missing 'fields' key"}
            
            # Convert to Pydantic model for validation
            report = COREPReport(**data)

            self._calculate_missing_total(report)
            
            return {"success": True, "report": report}
            
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse LLM response as JSON: {str(e)}"}
        except Exception as e:
            return {"error": f"Generation failed: {str(e)}"}
    
    def _calculate_missing_total(self, report: COREPReport):
        """
        Calculate total own funds if components exist but total is missing.
        """
        field_map = {f.field_code: f for f in report.fields}
        
        # Get component values
        cet1 = field_map.get("OF_010")
        at1 = field_map.get("OF_020")
        tier2 = field_map.get("OF_030")
        total = field_map.get("OF_040")
        
        if total and total.value is None:
            components = []
            for comp in [cet1, at1, tier2]:
                if comp and comp.value is not None:
                    components.append(comp.value)
            
            if len(components) == 3:
                total_value = sum(components)
                total.value = total_value
                total.justification = "Calculated as sum of CET1 + AT1 + Tier 2"
                total.source_rule = "CRR Article 72"
                total.confidence = min(cet1.confidence, at1.confidence, tier2.confidence)
