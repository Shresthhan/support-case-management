from app.ai.schemas import TriageInput
from app.ai.schemas import TriageSuggestion
from app.models.case import CategoryEnum
from app.models.case import PriorityEnum


def generate_mock_suggestion(
    triage_input: TriageInput,
) -> TriageSuggestion:
    """
    Return a local deterministic suggestion.

    It exists so the feature can be tested locally.
    """
    text = (
        f"{triage_input.title} "
        f"{triage_input.description}"
    ).lower()

    if any(
        word in text
        for word in [
            "password",
            "login",
            "account",
            "access",
        ]
    ):
        category = CategoryEnum.ACCOUNT
        priority = PriorityEnum.HIGH
        next_step = (
            "Verify the user's identity and check "
            "account access or password status."
        )

    elif any(
        word in text
        for word in [
            "payment",
            "invoice",
            "charge",
            "billing",
        ]
    ):
        category = CategoryEnum.BILLING
        priority = PriorityEnum.HIGH
        next_step = (
            "Check the related payment or invoice "
            "records before replying."
        )

    elif any(
        word in text
        for word in [
            "error",
            "crash",
            "not working",
            "bug",
        ]
    ):
        category = CategoryEnum.TECHNICAL
        priority = PriorityEnum.MEDIUM
        next_step = (
            "Request the error details and reproduce "
            "the issue if possible."
        )

    else:
        category = CategoryEnum.OTHER
        priority = PriorityEnum.MEDIUM
        next_step = (
            "Review the case details and ask for "
            "missing information if necessary."
        )

    short_summary = (
        f"Possible {category.value.lower()} issue: "
        f"{triage_input.title}"
    )

    return TriageSuggestion(
        category=category,
        priority=priority,
        short_summary=short_summary,
        recommended_next_step=next_step,
    )