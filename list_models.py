"""Shows which Groq models your key can use: python list_models.py"""
import llm
print("\n".join(llm.available_models()))