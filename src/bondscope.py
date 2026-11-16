"""Week 11 prototype, Python 3.9+. Run from the repository root:
    python3 -m pip install openai==2.48.0 python-dotenv==1.2.1
    python3 src/bondscope.py --list-only
    python3 src/bondscope.py
Set LLM_API_KEY in the project-root .env file (see .env.example).
The live run uses LLM_API_KEY or OPENAI_API_KEY, or prompts for a hidden key.
Override the default model with LLM_MODEL.
"""
import argparse
import getpass
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE = "bondscope"
ROLES = {
    "brief.md": "case brief",
    "data_dictionary.md": "field definitions",
    "daily_summary.csv": "daily summary",
    "rubric.md": "judging criteria",
    "trade_register.csv": "trade register",
    "daily_summary.csv": "daily bond summary with indicative prices and last trade prices where available",
    "trade_register.csv": "partial register of confirmed bond trades included in the case sample",
}
QUESTION = "Какие материалы доступны участникам кейса BondScope и для чего нужен каждый файл?"
TOOL = {
    "type": "function",
    "function": {
        "name": "list_materials",
        "description": "List the available participant files and their roles for this case.",
        "parameters": {
            "type": "object",
            "properties": {"case_id": {"type": "string", "enum": [CASE]}},
            "required": ["case_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}


def list_materials(case_id):
    if case_id != CASE:
        raise ValueError("Unknown case")
    folder = ROOT / "cases" / case_id
    if folder.resolve() != folder:
        raise ValueError("Unexpected case directory")
    return [
        {"file": item.name, "role": ROLES.get(item.name, "participant attachment")}
        for item in sorted(folder.iterdir())
        if not item.is_symlink() and item.is_file()
        and item.suffix.lower() in {".md", ".txt", ".csv", ".pdf"}
        and not item.name.startswith(".")
    ]


def run(client, model):
    messages = [
        {"role": "system", "content": "Help the organizer in Russian. Base the inventory on observed tool results. Include each exact filename and explain its role."},
        {"role": "user", "content": QUESTION},
    ]
    print(f"Model: {model}\nRequest: {QUESTION}")
    first = client.chat.completions.create(
        model=model, messages=messages, tools=[TOOL], tool_choice="auto",
        parallel_tool_calls=False,
    )
    reply = first.choices[0].message
    if len(reply.tool_calls or []) != 1:
        raise ValueError("Expected one model-selected inventory call; demo incomplete.")
    call = reply.tool_calls[0]
    args = json.loads(call.function.arguments)
    if call.function.name != "list_materials" or args != {"case_id": CASE}:
        raise ValueError("Rejected unexpected tool or arguments")
    print(f"Tool call: {call.function.name}({args})")
    inventory = list_materials(args["case_id"])
    result = json.dumps(inventory, ensure_ascii=False)
    print(f"Tool result: {result}")
    messages.extend([
        {"role": "assistant", "tool_calls": [call.model_dump(exclude_none=True)]},
        {"role": "tool", "tool_call_id": call.id, "content": result},
    ])
    final = client.chat.completions.create(model=model, messages=messages).choices[0].message.content
    if not final or any(item["file"] not in final for item in inventory):
        raise ValueError("Incomplete inventory in final answer; inspect the tool result.")
    print(f"Final answer:\n{final}")


def main():
    parser = argparse.ArgumentParser(description="BondScope case inventory")
    parser.add_argument("--list-only", action="store_true", help="inspect local files without API calls")
    if parser.parse_args().list_only:
        print(json.dumps(list_materials(CASE), ensure_ascii=False, indent=2))
        return
    from dotenv import load_dotenv
    from openai import OpenAI, APIError

    load_dotenv(ROOT / ".env", override=False)
    key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or getpass.getpass("OpenAI API key: ")
    if not key.strip():
        raise SystemExit("Missing API key")
    try:
        run(OpenAI(api_key=key.strip(), timeout=30, max_retries=1), os.getenv("LLM_MODEL") or "gpt-4.1-mini")
    except APIError as exc:
        raise SystemExit(f"API request failed: {type(exc).__name__} (status {getattr(exc, 'status_code', None)})") from None
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()
