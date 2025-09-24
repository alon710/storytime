from pydantic_ai import Agent, RunContext
from src.schemas.image import ImageRequest
from src.schemas.approval import NeedsApproval, Finalized
from src.schemas.state import TurnResult, ChatState
from src.tools.images import generate_image


agent = Agent(
    "openai:gpt-4",
    result_type=TurnResult,
    deps_type=ChatState,
    system_prompt="You are an image generation assistant. Generate images based on user requests and wait for approval.",
)


@agent.tool
def create_image(ctx: RunContext[ChatState], request: ImageRequest) -> NeedsApproval:
    result = generate_image(request)
    return NeedsApproval(image_path=result.image_path, params_used=result.params_used)


@agent.tool
def check_approval(ctx: RunContext[ChatState]) -> bool:
    chat_history = ctx.deps
    if not chat_history or not chat_history.messages:
        return False

    approval_keywords = ["yes", "approve", "approved", "good", "ok", "okay", "accept", "great", "perfect", "looks good"]
    rejection_keywords = ["no", "reject", "rejected", "bad", "not good", "try again", "redo", "change"]

    user_messages = [msg.text.lower() for msg in chat_history.messages[-5:] if msg.role == "user"]
    if not user_messages:
        return False

    latest_user_message = user_messages[-1]

    approval_score = sum(1 for keyword in approval_keywords if keyword in latest_user_message)
    rejection_score = sum(1 for keyword in rejection_keywords if keyword in latest_user_message)

    return approval_score > rejection_score


@agent.tool
def finalize_conversation(ctx: RunContext[ChatState]) -> Finalized:
    return Finalized(message="Thank you! Your image has been generated successfully. Goodbye!")


async def process_request(request: ImageRequest, chat_state: ChatState) -> TurnResult:
    if check_approval(RunContext(deps=chat_state)):
        return finalize_conversation(RunContext(deps=chat_state))

    result = await agent.run(
        f"Generate an image with these parameters: style={request.style}, age={request.age}, gender={request.gender}, seed_image={request.seed_image_path}",
        deps=chat_state,
    )
    return result.data
