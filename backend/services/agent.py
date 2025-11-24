import openai
import os

class AgentService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            print("Warning: OPENAI_API_KEY not set. AI features will be disabled.")

    def _ensure_client(self):
        """Ensure OpenAI client is initialized, raise error if not available."""
        if not self.client:
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
        return self.client

    def generate_report(self, data_context: str, prompt_customization: str = ""):
        """
        Generate a report based on the provided data context.
        """
        try:
            client = self._ensure_client()
            response = client.chat.completions.create(
                model="gpt-4", # Or gpt-3.5-turbo
                messages=[
                    {"role": "system", "content": "You are a financial analyst agent. Generate a comprehensive report based on the provided data."},
                    {"role": "user", "content": f"Data Context:\n{data_context}\n\nCustom Instructions:\n{prompt_customization}"}
                ]
            )
            return response.choices[0].message.content
        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error generating report: {str(e)}"

agent_service = AgentService()
