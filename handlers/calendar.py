import re

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import ContextTypes

from database import log_user_activity

from services.calendar_service import (
    get_latest_calendars,
)


def get_calendar_button_name(title: str) -> str:
    title = re.sub(
        r"\s+",
        " ",
        title or "",
    ).strip()

    clean_title = re.sub(
        r"\s*\[Revised\]\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()

    lower = clean_title.lower()

    year_match = re.search(
        r"\b20\d{2}\b",
        clean_title,
    )

    year = year_match.group(0) if year_match else ""

    if "pharmacy" in lower:

        if "fall" in lower:
            return f"Pharmacy — Fall {year} Semester"

        if "spring" in lower:
            return f"Pharmacy — Spring {year} Semester"

        if "summer" in lower:
            return f"Pharmacy — Summer {year} Semester"

        return f"Pharmacy — {year}"

    if "undergraduate" in lower:

        if "summer" in lower:
            return f"Summer {year} Trimester Undergraduate"

        if "spring" in lower:
            return f"Spring {year} Trimester Undergraduate"

        if "fall" in lower:
            return f"Fall {year} Trimester Undergraduate"

        return f"{year} Undergraduate"

    if "graduate" in lower:

        if "summer" in lower:
            return f"Summer {year} Trimester Graduate"

        if "spring" in lower:
            return f"Spring {year} Trimester Graduate"

        if "fall" in lower:
            return f"Fall {year} Trimester Graduate"

        return f"{year} Graduate"

    return clean_title


async def academic_calendar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    if update.effective_user:
        log_user_activity(
            update.effective_user.id,
            update.effective_user.first_name,
            update.effective_user.username,
        )

    try:
        calendars = await get_latest_calendars(5)

        if not calendars:
            await update.message.reply_text("⚠️ No academic calendars found right now.")
            return

        text = (
            "📅 <b>Academic Calendar</b>\n\n"
            "📌 Tap the button below each calendar "
            "to open the original UIU page.\n"
        )

        buttons = []

        for index, calendar in enumerate(
            calendars,
            start=1,
        ):
            title = calendar.get(
                "title",
                "Academic Calendar",
            )

            year = calendar.get(
                "year",
                "",
            )

            url = calendar.get(
                "url",
                "",
            )

            button_name = get_calendar_button_name(title)

            text += f"\n<b>{index}. {title}</b>\n" f"📅 {year}\n"

            if url:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            f"📄 {button_name} ↗",
                            url=url,
                        )
                    ]
                )

        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )

    except Exception as e:
        print(
            "Academic calendar error:",
            e,
        )

        await update.message.reply_text(
            "⚠️ Unable to load academic calendars right now."
        )
