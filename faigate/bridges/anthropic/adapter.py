"""Anthropic <-> canonical model adapters.

This module intentionally contains only normalization logic. Routing, policy
application, hook execution, and provider selection stay in the existing gate
core and are addressed through the ``CanonicalChatExecutor`` contract.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from ...api.anthropic.models import (
    AnthropicBridgeError,
    AnthropicContentBlock,
    AnthropicMessage,
    AnthropicMessagesRequest,
    AnthropicMessagesResponse,
    parse_anthropic_messages_request,
)
from ...canonical import (
    CanonicalChatExecutor,
    CanonicalChatRequest,
    CanonicalChatResponse,
    CanonicalMessage,
    CanonicalResponseMessage,
    CanonicalTool,
)


def anthropic_request_to_canonical(
    request: AnthropicMessagesRequest,
    *,
    headers: dict[str, str] | None = None,
) -> CanonicalChatRequest:
    """Map an Anthropic messages request to the internal gateway model."""

    normalized_headers = {str(key): str(value) for key, value in (headers or {}).items()}
    source = (
        normalized_headers.get("x-faigate-client")
        or normalized_headers.get("anthropic-client")
        or "claude-code"
    )
    client = source
    metadata = dict(request.metadata)
    metadata.setdefault("source", source)
    metadata.setdefault("bridge_surface", "anthropic-messages")
    if normalized_headers:
        metadata["bridge_headers"] = normalized_headers

    return CanonicalChatRequest(
        client=client,
        surface="anthropic-messages",
        requested_model=request.model,
        system=request.system,
        messages=[_message_to_canonical(message) for message in request.messages],
        tools=[
            CanonicalTool(
                name=tool.name,
                description=tool.description,
                input_schema=dict(tool.input_schema),
            )
            for tool in request.tools
        ],
        stream=request.stream,
        metadata=metadata,
    )


def canonical_to_openai_body(request: CanonicalChatRequest) -> dict[str, Any]:
    """Build the current internal handoff shape for the gateway core."""

    return request.to_openai_body()


def canonical_response_to_anthropic(
    response: CanonicalChatResponse,
    *,
    requested_model: str,
) -> AnthropicMessagesResponse:
    """Map the canonical response model back to Anthropic wire format."""

    return AnthropicMessagesResponse(
        id=response.response_id or f"msg_{uuid4().hex}",
        model=response.model or requested_model,
        content=_canonical_content_to_anthropic_blocks(response.message),
        stop_reason=response.stop_reason or response.message.stop_reason,
        usage=dict(response.usage),
        metadata={
            **dict(response.metadata),
            **({"provider": response.provider} if response.provider else {}),
        },
    )


async def dispatch_anthropic_messages(
    *,
    payload: dict[str, Any],
    headers: dict[str, str],
    executor: CanonicalChatExecutor,
) -> AnthropicMessagesResponse:
    """Run the full bridge flow for one Anthropic messages request."""

    wire_request = parse_anthropic_messages_request(payload)
    canonical_request = anthropic_request_to_canonical(wire_request, headers=headers)
    canonical_response = await executor.execute_canonical_chat(canonical_request)
    return canonical_response_to_anthropic(
        canonical_response,
        requested_model=wire_request.model,
    )


def _message_to_canonical(message: AnthropicMessage) -> CanonicalMessage:
    if any(block.type != "text" for block in message.content):
        raise AnthropicBridgeError(
            "Anthropic bridge v1 currently supports only text content blocks in messages"
        )
    if len(message.content) == 1 and message.content[0].type == "text":
        content: Any = message.content[0].text or ""
    else:
        content = [_anthropic_block_to_payload(block) for block in message.content]
    return CanonicalMessage(role=message.role, content=content)


def _anthropic_block_to_payload(block: AnthropicContentBlock) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": block.type}
    if block.text is not None:
        payload["text"] = block.text
    if block.tool_use_id:
        payload["tool_use_id"] = block.tool_use_id
    if block.name:
        payload["name"] = block.name
    if block.input:
        payload["input"] = dict(block.input)
    if block.metadata:
        payload["metadata"] = dict(block.metadata)
    return payload


def _canonical_content_to_anthropic_blocks(
    message: CanonicalResponseMessage,
) -> list[AnthropicContentBlock]:
    content = message.content
    blocks: list[AnthropicContentBlock]
    if isinstance(content, str):
        blocks = [AnthropicContentBlock(type="text", text=content)]
    elif isinstance(content, list):
        blocks = []
        for item in content:
            if isinstance(item, str):
                blocks.append(AnthropicContentBlock(type="text", text=item))
                continue
            if not isinstance(item, dict):
                blocks.append(AnthropicContentBlock(type="text", text=str(item)))
                continue
            blocks.append(
                AnthropicContentBlock(
                    type=str(item.get("type", "text") or "text"),
                    text=item.get("text"),
                    tool_use_id=str(item.get("tool_use_id", "") or "").strip() or None,
                    name=str(item.get("name", "") or "").strip() or None,
                    input=dict(item.get("input", {}) or {}),
                    metadata=dict(item.get("metadata", {}) or {}),
                )
            )
    else:
        blocks = [AnthropicContentBlock(type="text", text=str(content or ""))]

    for tool_call in message.tool_calls:
        if not isinstance(tool_call, dict):
            continue
        function = tool_call.get("function", {}) or {}
        raw_arguments = str(function.get("arguments", "") or "").strip()
        parsed_arguments: dict[str, Any]
        if raw_arguments:
            try:
                loaded = json.loads(raw_arguments)
                parsed_arguments = loaded if isinstance(loaded, dict) else {"arguments": loaded}
            except json.JSONDecodeError:
                parsed_arguments = {"raw_arguments": raw_arguments}
        else:
            parsed_arguments = {}
        blocks.append(
            AnthropicContentBlock(
                type="tool_use",
                tool_use_id=str(tool_call.get("id", "") or "").strip() or None,
                name=str(function.get("name", "") or "").strip() or None,
                input=parsed_arguments,
            )
        )
    return blocks
