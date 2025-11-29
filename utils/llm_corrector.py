"""LLM-based transcription correction utilities"""
import openai

def correct_transcript(
    transcript: str,
    provider: str = "openai",
    model: str = "gpt-3.5-turbo",
    custom_prompt: str = None,
    api_key: str = None
) -> str:
    """
    Correct transcription using LLM
    
    Args:
        transcript: Original transcript text
        provider: LLM provider ('openai', 'anthropic', 'local')
        model: Model name to use
        custom_prompt: Custom prompt for correction (optional)
        api_key: API key for the provider
    
    Returns:
        Corrected transcript text
    """
    if not api_key:
        raise ValueError("API key is required")
    
    # Default correction prompt
    default_prompt = """Please correct any errors in the following transcription, including grammar, punctuation, and factual accuracy. Maintain the original meaning and style. Return only the corrected text without additional commentary."""
    
    prompt = custom_prompt if custom_prompt else default_prompt
    full_prompt = f"{prompt}\n\nTranscription:\n{transcript}"
    
    if provider == "openai":
        print(f"Correcting transcript with OpenAI model: {model}")
        print(f"API key: {api_key}")
        print(f"Full prompt: {full_prompt}")
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that corrects transcriptions."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
    
    elif provider == "anthropic":
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=4000,
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

