import base64
from pathlib import Path
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.store.base import BaseStore
from src.schemas.state import State, NextAction
from src.schemas.seed_image import SeedImageData
from src.schemas.challenge import ChallengeData
from src.config import settings
from src.nodes.utils import extract_image_urls, ensure_pydantic_model, filter_image_content
from src.utils.images import generate_image
from src.file_store import temp_file_manager


def load_image_as_data_url(image_path: Path | str, mime_type: str) -> str:
    with open(file=str(image_path), mode="rb") as f:
        image_data = base64.b64encode(s=f.read()).decode(encoding="utf-8")
    return f"data:{mime_type};base64,{image_data}"


def validate_required_fields(seed_image_data: SeedImageData) -> None:
    if not seed_image_data.image_path:
        raise ValueError("Missing required field: image_path")


def seed_image_node(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    seed_image = ensure_pydantic_model(state.get("seed_image"), SeedImageData)
    challenge = ensure_pydantic_model(state.get("challenge"), ChallengeData)
    last_message = state["messages"][-1] if state["messages"] else None

    # Step 1: Check if approved
    if seed_image and seed_image.approved:
        return {"next_action": NextAction.CONTINUE}

    # Step 2: If last message was from AI, wait for user response
    if isinstance(last_message, AIMessage):
        return {"next_action": NextAction.END}

    # Initialize LLMs
    llm_conversational = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.seed_image.conversational_model,
        temperature=settings.seed_image.temperature,
        name="SEED_IMAGE_CONVERSATIONAL_LLM",
    )

    # Step 3: Try to generate image
    try:
        # Extract ALL reference images from messages (uploaded + previously generated)
        reference_image_urls = extract_image_urls(state["messages"])

        # Add previously generated images if this is a regeneration
        if seed_image and seed_image.previous_image_paths:
            for prev_path in seed_image.previous_image_paths:
                prev_image_url = load_image_as_data_url(prev_path, "image/png")
                reference_image_urls.append(prev_image_url)

        # Validate at least one reference image exists
        if not reference_image_urls:
            raise ValueError("No reference images provided. Please upload at least one photo of your child.")

        # Build prompt with challenge context
        base_prompt = settings.seed_image.system_prompt

        prompt_parts = [base_prompt]

        if challenge:
            prompt_parts.append("\n\nChild Details:")
            prompt_parts.append(f"- Name: {challenge.child.name}")
            prompt_parts.append(f"- Age: {challenge.child.age}")
            prompt_parts.append(f"- Gender: {challenge.child.gender}")

        # Add feedback if this is a regeneration
        if seed_image and seed_image.feedback:
            prompt_parts.append(f"\n\nParent Feedback: {seed_image.feedback}")
            prompt_parts.append("Please incorporate this feedback into the new image.")

        full_prompt = "\n".join(prompt_parts)

        # Generate image using Gemini
        image_output = generate_image(
            prompt=full_prompt,
            reference_image_urls=reference_image_urls,
            api_key=settings.google_api_key.get_secret_value(),
            model=settings.seed_image.model,
            temperature=settings.seed_image.temperature,
            max_output_tokens=settings.seed_image.max_tokens,
        )

        # Save generated image to temp file
        image_path_str = temp_file_manager.create_temp_file_from_base64(
            base64_data=image_output.image_base64, mime_type=image_output.mime_type, prefix="seed_image_"
        )
        image_path = Path(image_path_str)

        # Update previous_image_paths to include all references
        all_previous_paths: list[str | Path] = []
        if reference_image_urls:
            all_previous_paths.extend(reference_image_urls)
        if seed_image and seed_image.image_path:
            all_previous_paths.append(seed_image.image_path)

        # Create SeedImageData with new image
        new_seed_image = SeedImageData(
            image_path=image_path,
            prompt_used=image_output.prompt_used,
            mime_type=image_output.mime_type,
            previous_image_paths=[Path(p) if isinstance(p, str) else p for p in all_previous_paths],
            approved=False,
        )

        validate_required_fields(new_seed_image)

        # Create message with image
        image_data_url = load_image_as_data_url(image_path, image_output.mime_type)

        ai_message = AIMessage(
            content=[
                {
                    "type": "text",
                    "text": "I've generated a character reference image for your child. Please review it and let me know if you'd like any changes, or if you approve it and we can continue to creating the story!",
                },
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ]
        )

        return {
            "seed_image": new_seed_image,
            "messages": [ai_message],
            "next_action": NextAction.RETRY,
        }

    except Exception as e:
        # Step 4: Conversational fallback
        system_msg = SystemMessage(content=settings.seed_image.system_prompt)

        follow_up = llm_conversational.invoke(
            [
                system_msg,
                SystemMessage(
                    content=f"There was an issue generating the image: {str(e)}. "
                    "Ask the parent ONE specific question to help resolve this. "
                    "Be warm and friendly. DO NOT provide solutions or mention next steps."
                ),
            ]
            + filter_image_content(state["messages"])
        )

        return {
            "messages": [AIMessage(content=follow_up.content)],
            "next_action": NextAction.RETRY,
        }
