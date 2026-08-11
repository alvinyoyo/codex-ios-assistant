#!/usr/bin/env python3
"""Build a secret-free unsigned Shortcut that can be signed off-device.

The exported workflow asks for the receiver URL and token during import.  The
unsigned file therefore remains safe to send to a signing service, while the
private values are entered only on the iPhone.
"""

from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import plistlib


REPO = Path(__file__).resolve().parents[1]
PUBLIC_PLACEHOLDER = "__IOS_ASSISTANT_PUBLIC_URL__"
TOKEN_PLACEHOLDER = "__IOS_ASSISTANT_RECEIVER_TOKEN__"
URL_UUID = "A8AF2A8A-18F8-4A5D-A7E4-7F2E9F4B1001"
TOKEN_UUID = "A8AF2A8A-18F8-4A5D-A7E4-7F2E9F4B1002"
MATCH_UUID = "A8AF2A8A-18F8-4A5D-A7E4-7F2E9F4B1003"
ITEM_UUID = "A8AF2A8A-18F8-4A5D-A7E4-7F2E9F4B1004"
FETCH_UUID = "A8AF2A8A-18F8-4A5D-A7E4-7F2E9F4B1005"


def text_action(name: str, action_uuid: str, value: str) -> dict[str, object]:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "CustomOutputName": name,
            "UUID": action_uuid,
            "WFTextActionText": value,
        },
    }


def token_string(name: str, action_uuid: str, suffix: str = "") -> dict[str, object]:
    return {
        "Value": {
            "attachmentsByRange": {
                "{0, 1}": {
                    "OutputName": name,
                    "OutputUUID": action_uuid,
                    "Type": "ActionOutput",
                }
            },
            "string": "\ufffc" + suffix,
        },
        "WFSerializationType": "WFTextTokenString",
    }


def action_output(name: str, action_uuid: str) -> dict[str, str]:
    return {"OutputName": name, "OutputUUID": action_uuid, "Type": "ActionOutput"}


def fetch_adapter_actions() -> list[dict[str, object]]:
    fetch_url = {
        "Value": {
            "attachmentsByRange": {
                "{0, 1}": action_output("Receiver URL", URL_UUID),
                "{14, 1}": action_output("Item from List", ITEM_UUID),
            },
            "string": "\ufffc/v1/commands/\ufffc",
        },
        "WFSerializationType": "WFTextTokenString",
    }
    headers = {
        "Value": {
            "WFDictionaryFieldValueItems": [
                {
                    "WFItemType": 0,
                    "WFKey": {
                        "Value": {"string": "X-Auth"},
                        "WFSerializationType": "WFTextTokenString",
                    },
                    "WFValue": token_string("Receiver Token", TOKEN_UUID),
                }
            ]
        },
        "WFSerializationType": "WFDictionaryFieldValue",
    }
    return [
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.text.match",
            "WFWorkflowActionParameters": {
                "UUID": MATCH_UUID,
                "WFMatchTextCaseSensitive": True,
                "WFMatchTextPattern": "[a-f0-9]{64}",
                "text": {
                    "Value": {
                        "attachmentsByRange": {"{0, 1}": {"Type": "ExtensionInput"}},
                        "string": "\ufffc",
                    },
                    "WFSerializationType": "WFTextTokenString",
                },
            },
        },
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
            "WFWorkflowActionParameters": {
                "UUID": ITEM_UUID,
                "WFInput": {
                    "Value": action_output("Matches", MATCH_UUID),
                    "WFSerializationType": "WFTextTokenAttachment",
                },
                "WFItemSpecifier": "First Item",
            },
        },
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
            "WFWorkflowActionParameters": {
                "ShowHeaders": True,
                "UUID": FETCH_UUID,
                "WFHTTPHeaders": headers,
                "WFHTTPMethod": "GET",
                "WFURL": fetch_url,
            },
        },
    ]


def replace_extension_input(value: object) -> object:
    if isinstance(value, dict):
        if value.get("Type") == "ExtensionInput":
            return action_output("Contents of URL", FETCH_UUID)
        return {key: replace_extension_input(item) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_extension_input(item) for item in value]
    return value


def replace_private_placeholders(value: object, counts: dict[str, int]) -> object:
    if isinstance(value, dict):
        inner = value.get("Value")
        if (
            value.get("WFSerializationType") == "WFTextTokenString"
            and isinstance(inner, dict)
            and inner.get("string") == TOKEN_PLACEHOLDER
        ):
            counts[TOKEN_PLACEHOLDER] += 1
            return token_string("Receiver Token", TOKEN_UUID)
        return {key: replace_private_placeholders(item, counts) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_private_placeholders(item, counts) for item in value]
    if isinstance(value, str) and value.startswith(PUBLIC_PLACEHOLDER + "/"):
        counts[PUBLIC_PLACEHOLDER] += 1
        return token_string("Receiver URL", URL_UUID, value[len(PUBLIC_PLACEHOLDER) :])
    return value


def build_workflow(actions: list[dict[str, object]]) -> dict[str, object]:
    counts = {PUBLIC_PLACEHOLDER: 0, TOKEN_PLACEHOLDER: 0}
    portable_actions = replace_private_placeholders(deepcopy(actions), counts)
    if counts != {PUBLIC_PLACEHOLDER: 4, TOKEN_PLACEHOLDER: 4}:
        raise SystemExit(f"Unexpected Shortcut placeholder counts: {counts}")
    portable_actions = replace_extension_input(portable_actions)
    workflow_actions = [
        text_action("Receiver URL", URL_UUID, PUBLIC_PLACEHOLDER),
        text_action("Receiver Token", TOKEN_UUID, TOKEN_PLACEHOLDER),
        *fetch_adapter_actions(),
        *portable_actions,
    ]
    return {
        "WFWorkflowIcon": {
            "WFWorkflowIconGlyphNumber": 61440,
            "WFWorkflowIconStartColor": 463140863,
        },
        "WFWorkflowActions": workflow_actions,
        "WFQuickActionSurfaces": [],
        "WFWorkflowInputContentItemClasses": ["WFStringContentItem"],
        "WFWorkflowClientVersion": "4033.0.4.3",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowImportQuestions": [
            {
                "ActionIndex": 0,
                "Category": "Parameter",
                "ParameterKey": "WFTextActionText",
                "Text": "Receiver HTTPS origin (for example https://iphone.example.com)",
                "DefaultValue": "https://iphone.example.com",
            },
            {
                "ActionIndex": 1,
                "Category": "Parameter",
                "ParameterKey": "WFTextActionText",
                "Text": "Receiver token from the private Windows config",
                "DefaultValue": TOKEN_PLACEHOLDER,
            },
        ],
        "WFWorkflowTypes": ["WFWorkflowTypeShowInSearch"],
        "WFWorkflowOutputContentItemClasses": [],
        "WFWorkflowHasShortcutInputVariables": True,
        "WFWorkflowHasOutputFallback": False,
    }


def main() -> int:
    source_path = REPO / "shortcut" / "actions.template.plist"
    destination = REPO / "build" / "ios-assistant-windows-unsigned.shortcut"
    with source_path.open("rb") as source:
        actions = plistlib.load(source)
    if not isinstance(actions, list) or len(actions) != 95:
        raise SystemExit("Expected the committed 95-action Shortcut template.")
    workflow = build_workflow(actions)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".shortcut.tmp")
    with temporary.open("wb") as output:
        plistlib.dump(workflow, output, fmt=plistlib.FMT_BINARY, sort_keys=False)
    os.replace(temporary, destination)
    print(destination)
    print("This file is unsigned and contains placeholders, not private configuration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
