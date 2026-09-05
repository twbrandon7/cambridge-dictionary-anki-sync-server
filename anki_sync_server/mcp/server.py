import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette

from anki_sync_server.mcp.auth import ApiKeyAuthMiddleware
from anki_sync_server.server.task_status import TaskStatus
from anki_sync_server.tasks.card_creation_task import add_cloze_note_task

mcp_server = MCPServer(
    name="anki-sync-server",
    instructions=(
        "MCP server for Cambridge Dictionary Anki Sync Server. "
        "Allows creating cloze deletion flashcards and tracking background sync tasks."
    ),
)


def ensure_cloze_syntax(word: str, example: str) -> str:
    """
    Ensure the example sentence contains at least one cloze deletion marker ({{c1::...}}).
    If missing, automatically wraps the first occurrence of `word` in {{c1::word}}.
    """
    if "{{c1::" in example:
        return example

    clean_word = word.strip()
    if not clean_word:
        return example

    # Match exact word with boundary first
    word_pattern = r"\b" + re.escape(clean_word) + r"\b"
    if re.search(word_pattern, example, re.IGNORECASE):
        return re.sub(
            word_pattern, r"{{c1::\g<0>}}", example, count=1, flags=re.IGNORECASE
        )

    # Fallback without boundary (for phrases or partial matches)
    fallback_pattern = re.escape(clean_word)
    if re.search(fallback_pattern, example, re.IGNORECASE):
        return re.sub(
            fallback_pattern, r"{{c1::\g<0>}}", example, count=1, flags=re.IGNORECASE
        )

    # If word not found in sentence, append as reference cloze
    return f"{example} ({{{{c1::{clean_word}}}}})"


@mcp_server.tool(
    name="create_flashcard",
    description=(
        "Create a cloze deletion vocabulary flashcard in Anki. "
        "Enqueues a background task and immediately returns taskId. "
        "If 'english_example' does not contain cloze syntax {{c1::...}}, "
        "the target word will be automatically wrapped in {{c1::word}}. "
        "Omitted optional fields default to empty strings."
    ),
)
def create_flashcard(
    word: str,
    english_example: str,
    english_definition: str,
    part_of_speech: str = "",
    definition_translation: str = "",
    example_translation: str = "",
    guide_word: str = "",
    cefr_level: str = "",
    code: str = "",
) -> Dict[str, Any]:
    """
    Create a cloze deletion vocabulary flashcard.

    Args:
        word: The target vocabulary word (e.g., 'extraordinary').
        english_example: Sentence demonstrating usage. If cloze markup is omitted,
                         the word will automatically be wrapped as {{c1::word}}.
        english_definition: Clear English explanation of the word.
        part_of_speech: Optional part of speech (noun, verb, adjective, adverb, etc.).
        definition_translation: Optional translation of the definition into user's language.
        example_translation: Optional translation of the example sentence.
        guide_word: Optional Cambridge guide word categorizing meaning (e.g. 'very unusual').
        cefr_level: Optional CEFR proficiency level (A1, A2, B1, B2, C1, C2).
        code: Optional dictionary code/variety (e.g., 'UK' or 'US').

    Returns:
        Dictionary containing taskId, status ('pending'), statusUrl, and createdAt timestamp.
    """
    cloze_example = ensure_cloze_syntax(word, english_example)

    note_data = {
        "word": word.strip(),
        "partOfSpeech": part_of_speech.strip(),
        "guideWord": guide_word.strip(),
        "englishDefinition": english_definition.strip(),
        "definitionTranslation": definition_translation.strip(),
        "cefrLevel": cefr_level.strip(),
        "code": code.strip(),
        "englishExample": cloze_example.strip(),
        "exampleTranslation": example_translation.strip(),
    }

    task = add_cloze_note_task.delay(note_data)

    return {
        "taskId": task.id,
        "status": "pending",
        "statusUrl": f"/api/v1/tasks/{task.id}",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "note": note_data,
    }


@mcp_server.tool(
    name="get_task_status",
    description="Check the current processing status and result of a background flashcard creation task.",
)
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Fetch the status of an asynchronous flashcard creation task.

    Args:
        task_id: The UUID returned by create_flashcard.

    Returns:
        Dictionary with task status ('pending', 'started', 'success', 'failure') and result details.
    """
    task_status = TaskStatus.get_task_status(task_id)
    if task_status is None:
        return {
            "taskId": task_id,
            "status": "not_found",
            "error": f"Task {task_id} not found",
        }
    return task_status


@mcp_server.tool(
    name="check_health",
    description="Check server health and verify connectivity.",
)
def check_health() -> Dict[str, Any]:
    """Verify that the Anki sync server is reachable and operational."""
    return {
        "status": "ok",
        "server": "Cambridge Dictionary Anki Sync Server",
        "version": "0.1.0",
    }


@mcp_server.prompt(
    name="create_vocabulary_card",
    description="Prompt to guide the LLM in extracting vocabulary and creating a cloze flashcard from context.",
)
def create_vocabulary_card(word: str, context: str = "") -> str:
    """Generate a prompt to guide LLMs in structured flashcard creation."""
    prompt_text = (
        f"Please create an Anki cloze vocabulary flashcard for the word: '{word}'.\n"
    )
    if context:
        prompt_text += f'Context sentence: "{context}"\n'
    prompt_text += (
        "\nProvide:\n"
        "1. Part of speech (noun, verb, adjective, etc.)\n"
        "2. Clear English definition\n"
        "3. Definition translation in the user's preferred language\n"
        "4. Example sentence with the target word\n"
        "5. Example sentence translation\n"
        "6. CEFR level if known (e.g. B1, B2, C1)\n\n"
        "Then call the `create_flashcard` tool with these fields."
    )
    return prompt_text


def create_mcp_app(
    auth_middleware: bool = True,
    transport_security: Optional[TransportSecuritySettings] = None,
) -> Any:
    """
    Create and configure the Starlette Streamable HTTP MCP application.
    """
    if transport_security is None:
        transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False
        )

    base_app = mcp_server.streamable_http_app(
        streamable_http_path="/mcp",
        transport_security=transport_security,
    )

    if auth_middleware:
        return ApiKeyAuthMiddleware(base_app)
    return base_app
