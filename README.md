# Storytime - Children's Book Generator

Minimal LangGraph workflow: Discovery → Seed Image → Done

## Quick Start

```bash
pip install -e .
cp .env.example .env
# Add your API keys to .env
langgraph dev
```

## Workflow

1. **Discovery** - Chat about child & challenge (name, age, gender: boy/girl, challenge description)
2. **Seed Image** - Generate character illustration
3. **Complete** - Done!

## Structure

```
storytime_agent/
├── config.py           # Settings
├── state.py            # Minimal state
├── graph.py            # Workflow
├── nodes/
│   ├── discovery.py    # Challenge discovery
│   └── seed_image.py   # Image generation
└── schemas/
    └── challenge.py    # Challenge model
```

## Environment Variables

```env
LANGSMITH_API_KEY=lsv2_...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
LLM_MODEL=gpt-4
```

## Usage

1. Open Studio: `http://localhost:2024/studio`
2. Or use Agent Chat UI: `https://agentchat.vercel.app`
3. Configure: `http://localhost:2024` + assistant `storytime_agent`
4. Start chatting!
