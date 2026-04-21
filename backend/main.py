import os
import re
import zlib
import base64
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI

load_dotenv()

_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
_MODEL = "gpt-4o-mini"
_SYSTEM_INSTRUCTION = """You are an expert software analyst specializing in use case modeling (Cockburn style, UML 2.5).

OUTPUT FORMAT:
- Respond with ONLY the raw JSON object. No markdown, no code blocks, no preamble, no explanation.
- JSON keys are always in English. ALL values (actor names, use case names, trigger text, conditions, steps, scenarios) must be in the EXACT SAME LANGUAGE as the input requirement.
- LANGUAGE RULE IS ABSOLUTE: If the input is Turkish → every single value in the output must be Turkish. If English → English. Never mix. Inferred/implied use cases must also follow the input language.
  ✅ Turkish input → "Randevu Talep Et", "Müşteri", "Randevu İptal Et"
  ❌ Turkish input → "Request Appointment", "Customer", "Cancel Appointment"

NAMING CONVENTION:
- Use case names: "Verb + Noun" imperative format only.
  ✅ "Place Order", "Sipariş Ver", "Cancel Payment", "Ödemeyi İptal Et"
  ❌ "Ordering Process", "User places order", "Sipariş Verme İşlemi"
- Actor names: roles only, never person names.
  ✅ "Customer", "Müşteri", "Payment Gateway", "Admin"
  ❌ "Ahmet", "John", "The user"

GRANULARITY RULE (Cockburn User Goal Level):
- Each use case = one business goal completable in 2–20 minutes in one session.
- Never write UI interactions as use cases.
  ✅ "Place Order" (business goal)
  ❌ "Click Button", "Fill Form", "Submit Page"

ACTOR TAXONOMY — use exactly one of these types:
- "primary"         : initiates the use case, has the primary goal
- "secondary"       : supports or is called upon (staff, approver, operator)
- "external_system" : external system that participates (Payment Gateway, Email Service, SMS API, etc.)

TRIGGER RULE:
- Must be a concrete event, not an intention.
  ✅ "Customer clicks 'Place Order' on the checkout page"
  ✅ "Scheduler fires at 02:00 AM daily"
  ❌ "Customer wants to order", "User needs to pay"

RELATIONSHIP RULES:
- "include": use case A ALWAYS and UNCONDITIONALLY invokes use case B every single time.
  ✅ "Place Order" includes "Authenticate User"  (auth happens every time)
  ❌ "Request Appointment" includes "Approve Appointment"  (wrong — approval is not guaranteed)
- "extend": use case B is triggered only under a specific condition OR is mutually exclusive with another path.
  ✅ "Apply Coupon" extends "Place Order"  (optional)
  ✅ "Approve Appointment" extends "Request Appointment"  (one of two possible outcomes)
  ✅ "Reject Appointment" extends "Request Appointment"  (the other outcome)
- CRITICAL: When two use cases are mutually exclusive outcomes (approve/reject, accept/decline, success/fail), BOTH must use "extend", never "include".
- source and target values must EXACTLY match a name in actors[].use_cases.

DOMAIN COMPLETENESS RULE:
- Even if the requirement text is short, always infer the full set of standard use cases for that domain.
- Every workflow needs: registration/login, the core action, cancellation/undo, history/status view, and notification.
- Always add a Notification Service (external_system) actor if the system sends any emails, SMS, or push notifications.
- All inferred use case names must be in the input language (Turkish input → Turkish use case names).
  ✅ Turkish appointment system → "Kayıt Ol", "Randevu Talep Et", "Randevu İptal Et", "Randevu Geçmişini Görüntüle", "Bildirim Gönder"
  ✅ English appointment system → "Register", "Request Appointment", "Cancel Appointment", "View History", "Send Notification"

ALTERNATE FLOW TYPES — use exactly one of:
- "alternate"  : valid variation of the main flow (e.g., VIP gets automatic discount)
- "exception"  : error or failure condition (e.g., payment declined, stock unavailable)
- "extension"  : optional behavior added to the flow (e.g., save cart for later)

ALTERNATE FLOW COMPLETENESS:
- Always generate at least 4 alternate flows covering: a happy-path variation, a user-caused exception, a system-caused exception, and an optional extension.
- For approval workflows always include: requester cancels before decision, approver requests more info, timeout/no response scenario.

SUGGESTED SCENARIOS — look specifically for:
1. Edge cases: boundary values, empty states, timeouts, last item in stock
2. Security/permission: unauthorized access, session expiry, privilege escalation, IDOR
3. Logical gaps: missing prerequisites, concurrent modification, rollback needed
4. Concurrency: two users acting on the same resource simultaneously
5. Compliance: GDPR/KVKK data handling, audit logs, data retention, accessibility
6. Recovery: mid-flow system crash, network failure, browser refresh/back button

SELF-CHECK before outputting JSON — verify:
1. Every actor has at least one use case.
2. All use case names are in "Verb + Noun" imperative format.
3. External systems (payment gateways, email/SMS services, notification services) are included as "external_system" actors.
4. Trigger is a concrete event, not an intention.
5. Every relationship source/target exactly matches a name in actors[].use_cases.
6. Values are in the same language as the input.
7. No mutually exclusive outcomes (approve/reject, accept/decline) are linked with "include" — they must use "extend".
8. Domain completeness: registration, core action, cancellation, history/status, and notification use cases are all present.
9. At least 4 alternate flows are present.
Fix any violation before responding. If you fail to provide valid JSON the system will crash."""

app = FastAPI(title="FlowGenAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANALYZE_PROMPT = """Analyze the business requirement below and return a structured use case as strict JSON.

--- SCHEMA (use EXACTLY these key names) ---
{{
  "actors": [
    {{
      "name": "string",
      "type": "primary | secondary | external_system",
      "use_cases": ["Verb Noun", "Verb Noun"]
    }}
  ],
  "trigger": "string — concrete event that starts the main flow",
  "alternate_flows": [
    {{
      "type": "alternate | exception | extension",
      "condition": "string",
      "actor": "string — actor name involved",
      "steps": ["string", "string"]
    }}
  ],
  "relationships": [
    {{
      "type": "include | extend",
      "source": "exact use case name from actors[].use_cases",
      "target": "exact use case name from actors[].use_cases"
    }}
  ],
  "suggested_scenarios": ["string", "string"]
}}

--- EXAMPLE (hotel booking, English input → English output) ---
{{
  "actors": [
    {{ "name": "Guest", "type": "primary", "use_cases": ["Search Room", "Make Reservation", "Cancel Reservation"] }},
    {{ "name": "Receptionist", "type": "secondary", "use_cases": ["Confirm Booking", "Issue Refund"] }},
    {{ "name": "Payment Gateway", "type": "external_system", "use_cases": ["Process Payment", "Process Refund"] }}
  ],
  "trigger": "Guest clicks 'Book Now' on the room detail page",
  "alternate_flows": [
    {{ "type": "exception", "condition": "Payment is declined", "actor": "Payment Gateway", "steps": ["Gateway returns failure code", "System notifies Guest", "Guest is prompted to retry or use different card"] }},
    {{ "type": "alternate", "condition": "Guest is a loyalty member", "actor": "Guest", "steps": ["System applies loyalty discount automatically", "Updated total is shown before confirmation"] }},
    {{ "type": "extension", "condition": "Guest wants travel insurance", "actor": "Guest", "steps": ["Guest selects insurance add-on", "System adds insurance fee to total"] }}
  ],
  "relationships": [
    {{ "type": "include", "source": "Make Reservation", "target": "Process Payment" }},
    {{ "type": "extend", "source": "Cancel Reservation", "target": "Process Refund" }}
  ],
  "suggested_scenarios": [
    "Two guests book the last available room simultaneously (concurrency conflict)",
    "Session expires mid-booking — reservation state must be rolled back",
    "GDPR: Guest requests deletion of booking history",
    "Accessibility: screen-reader compatibility for date picker"
  ]
}}

--- NEGATIVE EXAMPLES (never do these) ---
❌ Use case as UI step: "Click Book Button", "Fill Guest Form"
❌ Actor as person name: "Ahmet", "John"
❌ Use case as noun phrase: "Reservation Management", "Payment Process"
❌ Trigger as intention: "Guest wants to book a room"
❌ Relationship target not matching an exact use case name

--- REQUIREMENT ---
{requirement}"""


# ── JSON safety net ───────────────────────────────────────────────────────────

def clean_json_response(raw: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    return json.loads(cleaned)


# ── Pydantic models ───────────────────────────────────────────────────────────

class RequirementRequest(BaseModel):
    requirement: str


class Actor(BaseModel):
    name: str
    type: str  # "primary" | "secondary" | "external_system"
    use_cases: list[str]


class AlternateFlow(BaseModel):
    type: str  # "alternate" | "exception" | "extension"
    condition: str
    actor: str
    steps: list[str]


class Relationship(BaseModel):
    type: str   # "include" | "extend"
    source: str
    target: str


class DiagramRequest(BaseModel):
    actors: list[Actor]
    trigger: str
    alternate_flows: list[AlternateFlow]
    relationships: list[Relationship]
    suggested_scenarios: list[str]


# ── Shared helpers ────────────────────────────────────────────────────────────

def _safe_id(text: str) -> str:
    return (
        text.replace(" ", "_").replace(".", "").replace("(", "").replace(")", "")
            .replace(",", "").replace("'", "").replace('"', "").replace("/", "_")
            .replace(":", "").replace("-", "_").replace("İ", "I").replace("ı", "i")
            .replace("ş", "s").replace("ğ", "g").replace("ü", "u")
            .replace("ö", "o").replace("ç", "c").replace("Ş", "S")
    )[:40]


def _build_uc_index(actors: list[Actor]) -> dict[str, str]:
    """Map use case name → node id for relationship lookups."""
    index = {}
    for a_idx, actor in enumerate(actors):
        for uc_idx, uc in enumerate(actor.use_cases):
            index[uc] = f"UC_{a_idx}_{uc_idx}"
    return index


# ── PlantUML ──────────────────────────────────────────────────────────────────

def _encode_plantuml(uml: str) -> str:
    data = zlib.compress(uml.encode("utf-8"))[2:-4]
    CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    res, i = [], 0
    while i < len(data):
        b0 = data[i] if i < len(data) else 0
        b1 = data[i + 1] if i + 1 < len(data) else 0
        b2 = data[i + 2] if i + 2 < len(data) else 0
        res.append(CHARS[(b0 >> 2) & 0x3F])
        res.append(CHARS[((b0 & 0x3) << 4) | ((b1 >> 4) & 0xF)])
        res.append(CHARS[((b1 & 0xF) << 2) | ((b2 >> 6) & 0x3)])
        res.append(CHARS[b2 & 0x3F])
        i += 3
    return "".join(res)


# Colors per actor type
_PUML_ACTOR_COLOR = {
    "primary": "#4F46E5",
    "secondary": "#0891B2",
    "external_system": "#6B7280",
}
_PUML_UC_COLOR = {
    "primary": "#EEF2FF",
    "secondary": "#E0F2FE",
    "external_system": "#F3F4F6",
}
_ALT_BORDER = {
    "alternate": "#0891B2",
    "exception": "#DC2626",
    "extension": "#059669",
}


def _build_plantuml(data: DiagramRequest) -> str:
    uc_index = _build_uc_index(data.actors)

    lines = [
        "@startuml",
        "left to right direction",
        "",
        "skinparam actorStyle awesome",
        "skinparam rectangle {",
        "  BackgroundColor #F8FAFF",
        "  BorderColor #C7D2FE",
        "}",
        "skinparam note {",
        "  BackgroundColor #FEF9C3",
        "  BorderColor #EAB308",
        "}",
        "skinparam usecase<<primary>> {",
        "  BackgroundColor #EEF2FF",
        "  BorderColor #4F46E5",
        "}",
        "skinparam usecase<<secondary>> {",
        "  BackgroundColor #E0F2FE",
        "  BorderColor #0891B2",
        "}",
        "skinparam usecase<<external_system>> {",
        "  BackgroundColor #F3F4F6",
        "  BorderColor #6B7280",
        "}",
        "skinparam usecase<<exception>> {",
        "  BackgroundColor #FFF0F0",
        "  BorderColor #DC2626",
        "}",
        "skinparam usecase<<alternate>> {",
        "  BackgroundColor #EFF6FF",
        "  BorderColor #0891B2",
        "}",
        "skinparam usecase<<extension>> {",
        "  BackgroundColor #F0FDF4",
        "  BorderColor #059669",
        "}",
        "skinparam usecase<<suggested>> {",
        "  BackgroundColor #F0FDF4",
        "  BorderColor #22C55E",
        "}",
        "",
    ]

    for idx, actor in enumerate(data.actors):
        color = _PUML_ACTOR_COLOR.get(actor.type, "#4F46E5")
        label = f' <<{actor.type}>>' if actor.type != "primary" else ""
        lines.append(f'actor "{actor.name}" as A{idx}{label} {color}')
    lines.append("")

    # System boundary
    lines.append('rectangle "System" {')

    # Use cases grouped by actor
    for a_idx, actor in enumerate(data.actors):
        for uc_idx, uc in enumerate(actor.use_cases):
            safe = uc.replace('"', "'")
            lines.append(f'  usecase "{safe}" as UC_{a_idx}_{uc_idx} <<{actor.type}>>')

    # Alternate / exception / extension use cases
    for j, alt in enumerate(data.alternate_flows):
        tag = f"[{alt.type}]"
        cond = alt.condition.replace('"', "'")
        lines.append(f'  usecase "{tag} {cond}" as UC_A{j} <<{alt.type}>>')

    # Suggested scenarios
    for k, sug in enumerate(data.suggested_scenarios):
        safe = sug.replace('"', "'")
        lines.append(f'  usecase "[?] {safe}" as UC_S{k} <<suggested>>')

    lines.append("}")
    lines.append("")

    # Actor → own use cases
    for a_idx, actor in enumerate(data.actors):
        for uc_idx in range(len(actor.use_cases)):
            lines.append(f"A{a_idx} --> UC_{a_idx}_{uc_idx}")

    # Actor → alternate flows
    for j, alt in enumerate(data.alternate_flows):
        matched = next(
            (i for i, a in enumerate(data.actors)
             if a.name.lower() in alt.actor.lower() or alt.actor.lower() in a.name.lower()),
            0,
        )
        style = "-->" if alt.type != "exception" else "-->"
        lines.append(f"A{matched} {style} UC_A{j}")

    # Suggested → primary actor
    for k in range(len(data.suggested_scenarios)):
        lines.append(f"A0 ..> UC_S{k} : <<suggested>>")

    # include / extend relationships
    lines.append("")
    for rel in data.relationships:
        src_id = uc_index.get(rel.source)
        tgt_id = uc_index.get(rel.target)
        if src_id and tgt_id:
            lines.append(f"{src_id} .> {tgt_id} : <<{rel.type}>>")

    # Trigger note
    if data.actors:
        first_uc = f"UC_0_0"
        trigger_safe = data.trigger.replace(":", "-").replace('"', "'")
        lines.append(f'\nnote top of {first_uc} : Trigger: {trigger_safe}')

    lines.append("@enduml")
    return "\n".join(lines)


# ── D2 + Kroki ────────────────────────────────────────────────────────────────

def _encode_kroki(source: str) -> str:
    compressed = zlib.compress(source.encode("utf-8"), 9)
    return base64.urlsafe_b64encode(compressed).decode("ascii")


_D2_ACTOR_FILL = {
    "primary":         ("#4F46E5", "#3730A3"),
    "secondary":       ("#0891B2", "#0E7490"),
    "external_system": ("#6B7280", "#4B5563"),
}
_D2_GROUP_FILL = {
    "primary":         "#EEF2FF",
    "secondary":       "#E0F2FE",
    "external_system": "#F3F4F6",
}
_D2_GROUP_STROKE = {
    "primary":         "#A5B4FC",
    "secondary":       "#7DD3FC",
    "external_system": "#D1D5DB",
}
_D2_ALT_FILL = {
    "alternate":  "#E0F2FE",
    "exception":  "#FEE2E2",
    "extension":  "#D1FAE5",
}
_D2_ALT_STROKE = {
    "alternate":  "#0891B2",
    "exception":  "#DC2626",
    "extension":  "#059669",
}


def _build_d2(data: DiagramRequest) -> str:
    uc_index = _build_uc_index(data.actors)

    lines = [
        "vars: {",
        "  d2-config: {",
        "    layout-engine: elk",
        "  }",
        "}",
        "",
    ]

    # Declare actors
    for idx, actor in enumerate(data.actors):
        actor_id = f"A{idx}"
        fill, stroke = _D2_ACTOR_FILL.get(actor.type, ("#4F46E5", "#3730A3"))
        shape = "person" if actor.type != "external_system" else "rectangle"
        lines += [
            f'{actor_id}: {actor.name} {{',
            f"  shape: {shape}",
            "  style: {",
            f'    fill: "{fill}"',
            '    font-color: "#ffffff"',
            f'    stroke: "{stroke}"',
            "  }",
            "}",
            "",
        ]

    # System
    lines += [
        "System: {",
        "  style: {",
        '    fill: "#F8FAFF"',
        '    stroke: "#C7D2FE"',
        "    stroke-width: 2",
        "  }",
        "",
    ]

    # Use case groups per actor
    for a_idx, actor in enumerate(data.actors):
        group_id = f"G{a_idx}"
        gfill  = _D2_GROUP_FILL.get(actor.type, "#EEF2FF")
        gstroke = _D2_GROUP_STROKE.get(actor.type, "#A5B4FC")
        lines += [
            f'  {group_id}: {actor.name} Use Cases {{',
            "    style: {",
            f'      fill: "{gfill}"',
            f'      stroke: "{gstroke}"',
            "    }",
        ]
        for uc_idx, uc in enumerate(actor.use_cases):
            label = uc.replace('"', "'")
            lines += [
                f'    UC_{a_idx}_{uc_idx}: "{label}" {{',
                "      shape: oval",
                "    }",
            ]
        lines += ["  }", ""]

    # Alternate flows grouped by type
    if data.alternate_flows:
        for alt_type in ["alternate", "exception", "extension"]:
            group_alts = [(j, a) for j, a in enumerate(data.alternate_flows) if a.type == alt_type]
            if not group_alts:
                continue
            gfill  = _D2_ALT_FILL[alt_type]
            gstroke = _D2_ALT_STROKE[alt_type]
            lines += [
                f'  {alt_type.capitalize()}_Flows: {alt_type.capitalize()} Flows {{',
                "    style: {",
                f'      fill: "{gfill}"',
                f'      stroke: "{gstroke}"',
                "    }",
            ]
            for j, alt in group_alts:
                cond = alt.condition.replace('"', "'")
                lines += [
                    f'    A{j}: "{cond}" {{',
                    "      shape: oval",
                    "    }",
                ]
            lines += ["  }", ""]

    # Suggested scenarios
    if data.suggested_scenarios:
        lines += [
            "  Suggested: {",
            "    style: {",
            '      fill: "#F0FDF4"',
            '      stroke: "#86EFAC"',
            "    }",
        ]
        for k, sug in enumerate(data.suggested_scenarios):
            label = sug.replace('"', "'")
            lines += [
                f'    S{k}: "{label}" {{',
                "      shape: oval",
                "      style: { stroke-dash: 5 }",
                "    }",
            ]
        lines += ["  }", ""]

    lines.append("}")
    lines.append("")

    # Actor → use case connections
    for a_idx, actor in enumerate(data.actors):
        for uc_idx in range(len(actor.use_cases)):
            lines.append(f'A{a_idx} -> System.G{a_idx}.UC_{a_idx}_{uc_idx}')

    # Actor → alternate flows
    for j, alt in enumerate(data.alternate_flows):
        matched_idx = next(
            (i for i, a in enumerate(data.actors)
             if a.name.lower() in alt.actor.lower() or alt.actor.lower() in a.name.lower()),
            0,
        )
        stroke = _D2_ALT_STROKE.get(alt.type, "#6B7280")
        group  = f"{alt.type.capitalize()}_Flows"
        lines += [
            f'A{matched_idx} -> System.{group}.A{j}: {{',
            f'  style: {{ stroke: "{stroke}" }}',
            "}",
        ]

    # Actor → suggested
    for k in range(len(data.suggested_scenarios)):
        lines += [
            f'A0 -> System.Suggested.S{k}: {{',
            '  style: { stroke-dash: 5; stroke: "#22C55E" }',
            "}",
        ]

    # include / extend relationships between use cases
    for rel in data.relationships:
        src_id = uc_index.get(rel.source)
        tgt_id = uc_index.get(rel.target)
        if not src_id or not tgt_id:
            continue
        src_actor_idx = int(src_id.split("_")[1])
        tgt_actor_idx = int(tgt_id.split("_")[1])
        stroke = "#4F46E5" if rel.type == "include" else "#059669"
        dash = "" if rel.type == "include" else "stroke-dash: 5;"
        lines += [
            f'System.G{src_actor_idx}.{src_id} -> System.G{tgt_actor_idx}.{tgt_id}: "<<{rel.type}>>" {{',
            f'  style: {{ stroke: "{stroke}"; {dash} }}',
            "}",
        ]

    # Trigger annotation
    trigger_safe = data.trigger.replace('"', "'")
    lines += [
        "",
        f'Trigger: "⚡ {trigger_safe}" {{',
        "  shape: text",
        '  style: { font-color: "#6B7280"; italic: true }',
        "}",
    ]

    return "\n".join(lines)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/api/analyze")
async def analyze_requirement(body: RequirementRequest):
    """Receive a business requirement, return structured use case JSON."""
    if not body.requirement.strip():
        raise HTTPException(status_code=400, detail="requirement cannot be empty")

    try:
        response = await _client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_INSTRUCTION},
                {"role": "user", "content": ANALYZE_PROMPT.format(requirement=body.requirement)},
            ],
            response_format={"type": "json_object"},
            max_tokens=2048,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")

    try:
        result = clean_json_response(response.choices[0].message.content.strip())
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {e}")

    return result


@app.post("/api/diagram")
async def generate_diagram(body: DiagramRequest):
    """Return PlantUML (styled) + D2 via Kroki diagrams."""
    if not body.actors:
        raise HTTPException(status_code=400, detail="actors list cannot be empty")

    plantuml_code = _build_plantuml(body)
    plantuml_url  = f"https://www.plantuml.com/plantuml/png/{_encode_plantuml(plantuml_code)}"

    d2_code = _build_d2(body)
    d2_url  = f"https://kroki.io/d2/svg/{_encode_kroki(d2_code)}"

    return {
        "plantuml_code": plantuml_code,
        "plantuml_url":  plantuml_url,
        "d2_code":       d2_code,
        "d2_url":        d2_url,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
