import logging

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from states import (
    SCHOLARSHIP_GPA,
    SCHOLARSHIP_PROGRAM,
    SCHOLARSHIP_SIZE,
    SCHOLARSHIP_CREDITS,
    SCHOLARSHIP_HIGHER_CHOICE,
    SCHOLARSHIP_HIGHER_COUNT,
)

from services.scholarship_service import (
    generate_estimate,
    generate_result_text,
    generate_ineligible_text,
    scholarship_rules_text,
    get_minimum_credits,
)

from keyboards import get_main_menu
from database import log_user_activity

logger = logging.getLogger(__name__)

PROGRAM_OPTIONS = [
    "BBA",
    "BBA in AIS",
    "BSECO",
    "BSCSE",
    "BSEEE",
    "BSDS",
    "B.Sc. in CE",
    "BSSEDS",
    "BSSMSJ",
    "BA in English",
    "B.Pharm",
    "BSBGE",
    "Graduate",
]


def cancel_keyboard():
    return ReplyKeyboardMarkup(
        [["❌ Cancel"]],
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
    )


def program_keyboard():
    rows = []
    current = []

    for program in PROGRAM_OPTIONS:
        current.append(program)

        if len(current) == 2:
            rows.append(current)
            current = []

    if current:
        rows.append(current)

    rows.append(["❌ Cancel"])

    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
    )


def higher_choice_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["📊 I have an estimate"],
            ["🤷 I don't know"],
            ["❌ Cancel"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
    )


def result_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 Calculate Again",
                    callback_data="scholarship_again",
                )
            ],
            [
                InlineKeyboardButton(
                    "📚 Scholarship Rules",
                    callback_data="scholarship_rules",
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Main Menu",
                    callback_data="scholarship_main_menu",
                )
            ],
        ]
    )


async def scholarship_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_user:
        log_user_activity(
            update.effective_user.id,
            update.effective_user.first_name,
            update.effective_user.username,
        )

    context.user_data["scholarship_data"] = {}

    await update.message.reply_text(
        "🎓 <b>Scholarship Chance Estimator</b>\n\n"
        "Let's estimate your merit scholarship chances.\n\n"
        "⚠️ This is an estimate, not an official UIU "
        "scholarship decision.\n\n"
        "<b>Step 1 of 4</b>\n\n"
        "Enter your <b>previous trimester/semester GPA</b>.\n\n"
        "Example: <code>3.78</code>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )

    return SCHOLARSHIP_GPA


async def scholarship_gpa(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        gpa = float(text)

        if gpa < 0 or gpa > 4:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "⚠️ Please enter a valid GPA between "
            "<b>0.00</b> and <b>4.00</b>.\n\n"
            "Example: <code>3.78</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )

        return SCHOLARSHIP_GPA

    context.user_data["scholarship_data"]["gpa"] = gpa

    if gpa < 3.50:
        eligibility = {
            "reason": "gpa",
            "minimum_gpa": 3.50,
            "gpa": gpa,
        }

        await update.message.reply_text(
            generate_ineligible_text(eligibility),
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )

        return SCHOLARSHIP_GPA

    await update.message.reply_text(
        "<b>Step 2 of 4</b>\n\n" "🎓 <b>Select your program:</b>",
        reply_markup=program_keyboard(),
        parse_mode="HTML",
    )

    return SCHOLARSHIP_PROGRAM


async def scholarship_program(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    program = update.message.text.strip()

    if program == "❌ Cancel":
        return await scholarship_cancel(update, context)

    if program not in PROGRAM_OPTIONS:
        await update.message.reply_text(
            "Please select a program from the keyboard.",
            reply_markup=program_keyboard(),
        )

        return SCHOLARSHIP_PROGRAM

    context.user_data["scholarship_data"]["program"] = program

    await update.message.reply_text(
        "<b>Step 3 of 4</b>\n\n"
        "👥 Approximately how many students are "
        "in your program?\n\n"
        "Example: <code>500</code>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )

    return SCHOLARSHIP_SIZE


async def scholarship_size(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        size = int(text)

        if size < 10 or size > 100000:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "⚠️ Please enter a reasonable student count.\n\n"
            "Minimum: <code>10</code>\n"
            "Maximum: <code>100000</code>\n\n"
            "Example: <code>500</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )

        return SCHOLARSHIP_SIZE

    data = context.user_data.setdefault(
        "scholarship_data",
        {},
    )

    data["total_students"] = size

    program = data.get("program")

    minimum_credits = get_minimum_credits(program)

    await update.message.reply_text(
        "📚 <b>Qualifying Credits</b>\n\n"
        "How many credits did you register in the "
        "qualifying trimester/semester?\n\n"
        f"Minimum required for <b>{program}</b>: "
        f"<b>{minimum_credits:g}</b> credits\n\n"
        "Example: <code>12</code>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )

    return SCHOLARSHIP_CREDITS


async def scholarship_credits(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        credits = float(text)

        if credits <= 0 or credits > 40:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "⚠️ Please enter a valid credit amount.\n\n" "Example: <code>12</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )

        return SCHOLARSHIP_CREDITS

    data = context.user_data.setdefault(
        "scholarship_data",
        {},
    )

    data["qualifying_credits"] = credits

    await update.message.reply_text(
        "<b>Step 4 of 4</b>\n\n"
        "📊 Do you have an idea how many students "
        "may have a higher GPA than you?",
        reply_markup=higher_choice_keyboard(),
        parse_mode="HTML",
    )

    return SCHOLARSHIP_HIGHER_CHOICE


async def scholarship_higher_choice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    choice = update.message.text.strip()

    if choice == "📊 I have an estimate":
        await update.message.reply_text(
            "Approximately how many students do you "
            "think may have a higher GPA than you?\n\n"
            "Example: <code>20</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )

        return SCHOLARSHIP_HIGHER_COUNT

    if choice == "🤷 I don't know":
        data = context.user_data.setdefault(
            "scholarship_data",
            {},
        )

        data["higher_students"] = None
        data["higher_students_source"] = "statistical_estimate"

        return await calculate_scholarship(
            update,
            context,
        )

    if choice == "❌ Cancel":
        return await scholarship_cancel(
            update,
            context,
        )

    await update.message.reply_text(
        "Please choose one of the available options.",
        reply_markup=higher_choice_keyboard(),
    )

    return SCHOLARSHIP_HIGHER_CHOICE


async def scholarship_higher_count(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    data = context.user_data.get(
        "scholarship_data",
        {},
    )

    try:
        higher = int(text)

        total_students = int(
            data.get(
                "total_students",
                0,
            )
        )

        if total_students <= 0:
            raise ValueError

        if higher < 0:
            raise ValueError

        if higher >= total_students:
            await update.message.reply_text(
                "⚠️ <b>Invalid estimate.</b>\n\n"
                f"Your program size is "
                f"<b>{total_students}</b> students.\n\n"
                "The number of students with a higher GPA "
                f"must be between <b>0</b> and "
                f"<b>{total_students - 1}</b>.",
                reply_markup=cancel_keyboard(),
                parse_mode="HTML",
            )

            return SCHOLARSHIP_HIGHER_COUNT

    except ValueError:
        await update.message.reply_text(
            "⚠️ Please enter a valid whole number.\n\n" "Example: <code>20</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )

        return SCHOLARSHIP_HIGHER_COUNT

    data["higher_students"] = higher
    data["higher_students_source"] = "user_estimate"

    return await calculate_scholarship(
        update,
        context,
    )


async def calculate_scholarship(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    data = context.user_data.get(
        "scholarship_data",
        {},
    )

    required = [
        "gpa",
        "program",
        "total_students",
        "qualifying_credits",
    ]

    missing = [key for key in required if key not in data]

    if missing:
        logger.error(
            "Scholarship data missing: %s | data=%s",
            missing,
            data,
        )

        await update.message.reply_text(
            "⚠️ Some required information is missing.\n\n"
            "Please start the calculator again.",
            reply_markup=cancel_keyboard(),
        )

        return SCHOLARSHIP_GPA

    try:
        result = generate_estimate(
            gpa=float(data["gpa"]),
            program=str(data["program"]),
            total_students=int(data["total_students"]),
            qualifying_credits=float(data["qualifying_credits"]),
            higher_students=(
                None
                if data.get("higher_students") is None
                else int(data["higher_students"])
            ),
        )

        if not isinstance(result, dict):
            raise TypeError("Scholarship service returned invalid result.")

        if not result.get("eligible", False):
            eligibility = result.get(
                "eligibility",
                {
                    "reason": "calculation_error",
                },
            )

            await update.message.reply_text(
                generate_ineligible_text(eligibility),
                reply_markup=cancel_keyboard(),
                parse_mode="HTML",
            )

            return SCHOLARSHIP_GPA

        result["estimate_source"] = data.get(
            "higher_students_source",
            "statistical_estimate",
        )

        result["is_exact"] = False

        context.user_data["scholarship_result"] = result

        result_text = generate_result_text(result)

        await update.message.reply_text(
            result_text,
            reply_markup=result_keyboard(),
            parse_mode="HTML",
        )

        context.user_data.pop(
            "scholarship_data",
            None,
        )

        return ConversationHandler.END

    except Exception as error:
        logger.exception(
            "Scholarship calculation failed. data=%s",
            data,
        )

        await update.message.reply_text(
            "⚠️ <b>Unable to complete the estimate.</b>\n\n"
            "The statistical estimate could not be generated "
            "right now.\n\n"
            "Please try again.",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )

        return SCHOLARSHIP_GPA


async def scholarship_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    if query.data == "scholarship_again":
        context.user_data["scholarship_data"] = {}

        await query.message.reply_text(
            "🎓 <b>Scholarship Chance Estimator</b>\n\n"
            "Let's create a new estimate.\n\n"
            "⚠️ This is an estimate, not an official UIU "
            "scholarship decision.\n\n"
            "<b>Step 1 of 4</b>\n\n"
            "Enter your <b>previous trimester/semester GPA</b>.\n\n"
            "Example: <code>3.78</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )

        return SCHOLARSHIP_GPA

    if query.data == "scholarship_rules":
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Result",
                        callback_data="scholarship_back",
                    )
                ]
            ]
        )

        await query.edit_message_text(
            scholarship_rules_text(),
            reply_markup=keyboard,
            parse_mode="HTML",
        )

        return

    if query.data == "scholarship_back":
        result = context.user_data.get("scholarship_result")

        if result:
            await query.edit_message_text(
                generate_result_text(result),
                reply_markup=result_keyboard(),
                parse_mode="HTML",
            )
        else:
            await query.edit_message_text(
                "🎓 <b>Scholarship Estimate</b>\n\n" "Please start a new calculation.",
                parse_mode="HTML",
            )

        return

    if query.data == "scholarship_main_menu":
        context.user_data.pop(
            "scholarship_data",
            None,
        )

        context.user_data.pop(
            "scholarship_result",
            None,
        )

        await query.message.reply_text(
            "🏠 Main Menu",
            reply_markup=get_main_menu(),
        )


async def scholarship_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.pop(
        "scholarship_data",
        None,
    )

    context.user_data.pop(
        "scholarship_result",
        None,
    )

    await update.message.reply_text(
        "❌ Scholarship estimation cancelled.",
        reply_markup=get_main_menu(),
    )

    return ConversationHandler.END
