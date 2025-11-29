"""LLM-based summarization utilities"""
import openai
# from anthropic import Anthropic

def summarize_text(
    text: str,
    provider: str = "openai",
    model: str = "gpt-3.5-turbo",
    summary_type: str = "Brief",
    max_length: int = 200,
    custom_prompt: str = None,
    api_key: str = None
) -> str:
    """
    Summarize text using LLM
    
    Args:
        text: Text to summarize
        provider: LLM provider ('openai', 'anthropic', 'local')
        model: Model name to use
        summary_type: Type of summary (Brief, Detailed, Bullet Points, Executive Summary)
        max_length: Approximate maximum length in words
        custom_prompt: Custom prompt for summarization (optional)
        api_key: API key for the provider
    
    Returns:
        Summary text
    """
    if not api_key:
        raise ValueError("API key is required")
    
    # Build prompt based on summary type
    if custom_prompt:
        prompt = custom_prompt
    else:
        type_instructions = {
            "Brief": "Create a brief, concise summary",
            "Detailed": "Create a detailed, comprehensive summary",
            "Bullet Points": "Create a summary in bullet point format",
            "Executive Summary": "Create an executive summary highlighting key points and decisions"
        }
        
        instruction = type_instructions.get(summary_type, "Create a summary")
        prompt = f"{instruction} of the following text in approximately {max_length} words. Return only the summary without additional commentary."
    
    full_prompt = f"{prompt}\n\nText:\n{text}"
    
    if provider == "openai":
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates summaries."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    
    elif provider == "anthropic":
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )
        return response.content[0].text.strip()
    
    elif provider == "local":
        # For local models, you would implement your own client here
        # This is a placeholder
        raise NotImplementedError("Local provider not yet implemented. Please use OpenAI or Anthropic.")
    
    else:
        raise ValueError(f"Unknown provider: {provider}")

