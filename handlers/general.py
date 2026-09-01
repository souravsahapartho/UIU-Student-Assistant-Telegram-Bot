import logging

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from telegram.ext import ContextTypes

from keyboards import (
    get_main_menu,
    get_links_keyboard,
)

from services.notice_service import get_cached_notices

from database import (
    log_user_activity,
    get_notification_status,
    toggle_notification,
)

logger = logging.getLogger(__name__)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.message.from_user

    log_user_activity(
        user.id,
        user.first_name,
        user.username,
    )

    welcome_msg = (
        f"👋 Welcome to **UIU Student Assistant**, {user.first_name}!\n\n"
        "Your personal assistant for:\n"
        "🎓 CGPA calculation\n"
        "💰 Tuition fee calculation\n"
        "🎁 Scholarship calculation\n"
        "📚 Academic resources\n"
        "🔗 Important UIU links\n"
        "📅 Academic calendar\n"
        "📢 Latest notices\n\n"
        "👨‍💻 _Made with ❤️ by @souravsahapartho_\n\n"
        "👇 Select an option from the menu below."
    )

    await update.message.reply_text(
        welcome_msg,
        reply_markup=get_main_menu(),
        parse_mode="Markdown",
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    help_text = (
        "❓ **Help Center**\n\n"
        "🎓 **CGPA Calculator**\n"
        "Calculate semester GPA and updated overall CGPA.\n\n"
        "💰 **Fee Calculator**\n"
        "Estimate tuition fees, retake fees, scholarships, "
        "waivers and installments.\n\n"
        "🎁 **Scholarship Calculator**\n"
        "Estimate your merit scholarship chances.\n\n"
        "📚 **Academic Information**\n"
        "Access important academic information.\n\n"
        "📢 **Notices**\n"
        "Get the latest UIU notices.\n\n"
        "🔗 **Important Links**\n"
        "Quick access to official UIU resources.\n\n"
        "If you face any issue, use /start to restart the bot."
    )

    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
    )


async def show_help(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await help_command(
        update,
        context,
    )


async def about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    about_text = (
        "🤖 **UIU Student Assistant**\n\n"
        "A student-focused Telegram assistant for "
        "United International University.\n\n"
        "Version 2.0.0\n\n"
        "👨‍💻 **Developer:** Sourav Saha\n"
        "📧 **Contact:** im@sourav.com.bd\n\n"
        "*Disclaimer:* Fee and academic policy information "
        "may change. Please verify important decisions with "
        "official UIU sources."
    )

    await update.message.reply_text(
        about_text,
        parse_mode="Markdown",
    )


async def show_about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await about(
        update,
        context,
    )


async def important_links(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = "🔗 **Important UIU Links**\n\n" "Select a link below to open it."

    await update.message.reply_text(
        text,
        reply_markup=get_links_keyboard(),
        parse_mode="Markdown",
    )


async def show_links(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await important_links(
        update,
        context,
    )


def get_academic_info_keyboard():
    keyboard = [
        [
            KeyboardButton("🎓 Admission"),
            KeyboardButton("📝 Registration"),
        ],
        [
            KeyboardButton("📊 Credit System"),
            KeyboardButton("🔄 Retake Rules"),
        ],
        [
            KeyboardButton("🎯 Graduation"),
            KeyboardButton("📚 Grading System"),
        ],
        [
            KeyboardButton("⬅️ Main Menu"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
    )


def grading_system_text():
    return (
        "📚 <b>UIU Grading System</b>\n\n"
        "<pre>"
        "Letter   Grade   Marks     Assessment\n"
        "────────────────────────────────────\n"
        "A        4.00    90–100    Outstanding\n"
        "A-       3.67    86–89     Excellent\n"
        "B+       3.33    82–85     Very Good\n"
        "B        3.00    78–81     Good\n"
        "B-       2.67    74–77     Above Average\n"
        "C+       2.33    70–73     Average\n"
        "C        2.00    66–69     Below Average\n"
        "C-       1.67    62–65     Poor\n"
        "D+       1.33    58–61     Very Poor\n"
        "D        1.00    55–57     Pass\n"
        "F        0.00    0–54      Fail\n"
        "</pre>\n\n"
        "📌 This grading scale is used for CGPA calculation."
    )


async def academic_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "📚 **Academic Information**\n\n" "Select a topic from the menu below:",
        reply_markup=get_academic_info_keyboard(),
        parse_mode="Markdown",
    )


async def academic_info_menu_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text

    if text == "⬅️ Main Menu":
        await academic_info_main_menu(
            update,
            context,
        )
        return

    if text == "🎓 Admission":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🌐 UIU Admission",
                    url="https://admission.uiu.ac.bd/Admission/Home.aspx",
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 Admission Criteria",
                    url="https://admission.uiu.ac.bd/Admission/Candidate/UndergraduateProgramCriteria.aspx",
                )
            ],
        ]

        await update.message.reply_text(
            "🎓 <b>Admission Information</b>\n\n"
            "Get information about UIU undergraduate and "
            "graduate admission, eligibility requirements, "
            "application procedures and admission test details.\n\n"
            "Use the buttons below to visit the official UIU "
            "admission resources.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    if text == "📝 Registration":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔐 UCAM",
                    url="https://ucam.uiu.ac.bd/",
                ),
                InlineKeyboardButton(
                    "☁️ UCAM Cloud",
                    url="https://uiu.ucamcloud.com/",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📖 Registration Guide",
                    url="https://ucam.uiu.ac.bd/Upload/RegistrationNotice/Instructions-for-self-registration.pdf",
                )
            ],
        ]

        await update.message.reply_text(
            "📝 <b>Course Registration</b>\n\n"
            "Course selection, section selection and course "
            "registration are generally handled through UIU's "
            "registration systems.\n\n"
            "Before registration, make sure your advising and "
            "other required conditions are completed.\n\n"
            "Use the buttons below to access the official "
            "registration systems and guide.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    if text == "📊 Credit System":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🌐 UIU Academic Information",
                    url="https://www.uiu.ac.bd/academics/",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎓 Admission & Program Credits",
                    url="https://admission.uiu.ac.bd/Admission/Home.aspx",
                )
            ],
        ]

        await update.message.reply_text(
            "📊 <b>Credit System</b>\n\n"
            "Every UIU academic program has a defined credit "
            "requirement for degree completion.\n\n"
            "Credit requirements can vary depending on the "
            "academic program and curriculum.\n\n"
            "For your exact program requirement, always verify "
            "the current curriculum and official UIU information.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    if text == "🔄 Retake Rules":
        keyboard = [
            [
                InlineKeyboardButton(
                    "📚 UIU Grading & Retake Policy",
                    url="https://www.uiu.ac.bd/academics/grading-performance-evaluation/",
                )
            ]
        ]

        await update.message.reply_text(
            "🔄 <b>Retake Rules</b>\n\n"
            "Students may retake a course when they want to "
            "improve their grade.\n\n"
            "A retake requires registering for the course again "
            "and paying the applicable tuition and other fees.\n\n"
            "⚠️ Retake policies can depend on the applicable "
            "academic rules, so always verify the latest policy "
            "from UIU.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    if text == "🎯 Graduation":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🌐 UIU Academic Information",
                    url="https://www.uiu.ac.bd/academics/",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎓 UIU Convocation",
                    url="https://convocation.uiu.ac.bd/",
                )
            ],
        ]

        await update.message.reply_text(
            "🎯 <b>Graduation Requirements</b>\n\n"
            "Graduation requirements depend on your academic "
            "program, completed credits, CGPA and other applicable "
            "degree requirements.\n\n"
            "Students should verify their exact degree requirements "
            "with their department and official UIU academic resources.\n\n"
            "Use the buttons below for official information.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    if text == "📚 Grading System":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🌐 Official UIU Grading System",
                    url="https://www.uiu.ac.bd/academics/grading-performance-evaluation/",
                )
            ]
        ]

        await update.message.reply_text(
            grading_system_text(),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return


async def academic_info_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🏠 **Main Menu**\n\n" "Select an option from the menu below.",
        reply_markup=get_main_menu(),
        parse_mode="Markdown",
    )


async def academic_info_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    if query.data == "acad_back":
        await query.edit_message_text("Use /start to return to the main menu.")
        return

    if query.data == "acad_back_info":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🎓 Admission",
                    url="https://admission.uiu.ac.bd/Admission/Home.aspx",
                ),
                InlineKeyboardButton(
                    "📝 Registration",
                    callback_data="acad_registration",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 Credit System",
                    callback_data="acad_credit",
                ),
                InlineKeyboardButton(
                    "🔄 Retake Rules",
                    callback_data="acad_retake",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎯 Graduation",
                    url="https://convocation.uiu.ac.bd/",
                ),
                InlineKeyboardButton(
                    "📚 Grading System",
                    callback_data="acad_grading",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Main Menu",
                    callback_data="acad_back",
                ),
            ],
        ]

        await query.edit_message_text(
            "📚 **Academic Information**\n\n" "Select a topic:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    if query.data == "acad_grading":
        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Academic Information",
                    callback_data="acad_back_info",
                )
            ]
        ]

        await query.edit_message_text(
            grading_system_text(),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    information = {
        "acad_registration": (
            "📝 **Registration**\n\n"
            "Course selection, section selection and "
            "course registration are handled through "
            "the official UIU registration systems.\n\n"
            "Please verify the latest registration notice "
            "before registering."
        ),
        "acad_credit": (
            "📊 **Credit System**\n\n"
            "Credit requirements depend on the academic "
            "program and curriculum.\n\n"
            "Please verify your exact program requirement "
            "from official UIU sources."
        ),
        "acad_retake": (
            "🔄 **Retake Rules**\n\n"
            "Retake and improvement policies may vary "
            "according to the applicable academic rules.\n\n"
            "Please verify the latest policy from UIU."
        ),
    }

    text = information.get(
        query.data,
        "Information not available.",
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Academic Information",
                callback_data="acad_back_info",
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def academic_calendar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = (
        "📅 **Academic Calendar**\n\n"
        "Please check the official UIU academic calendar "
        "for the latest dates and schedules."
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
    )


async def notices(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_user:
        log_user_activity(
            update.effective_user.id,
            update.effective_user.first_name,
            update.effective_user.username,
        )

    notices_list = await get_cached_notices(5)

    if notices_list:
        msg = "📢 <b>Latest UIU Notices:</b>\n\n"

        for idx, notice in enumerate(notices_list, 1):
            title = notice.get("title", "Untitled Notice")
            link = notice.get("link") or notice.get("url") or ""
            date_str = notice.get("published_date", "")

            msg += f"📌 <b>{idx}. {title}</b>\n"
            if date_str:
                msg += f"📅 <i>{date_str}</i>\n"
            if link:
                msg += f"🔗 <a href='{link}'>Read Full Notice</a>\n\n"
            else:
                msg += "\n"

        await update.message.reply_text(
            msg,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    else:
        await update.message.reply_text(
            "📢 No notices available right now. Please check back later."
        )


async def settings_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    status = get_notification_status(user_id)

    status_text = "🟢 ON" if status else "🔴 OFF"

    keyboard = [
        [
            InlineKeyboardButton(
                f"🔔 Notifications: {status_text}",
                callback_data="toggle_alerts",
            )
        ],
    ]

    await update.message.reply_text(
        "⚙️ **Settings**\n\n" "Manage your notification preferences.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def settings_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    if query.data == "toggle_alerts":
        user_id = query.from_user.id

        new_status = toggle_notification(user_id)

        status_text = "🟢 ON" if new_status else "🔴 OFF"

        keyboard = [
            [
                InlineKeyboardButton(
                    f"🔔 Notifications: {status_text}",
                    callback_data="toggle_alerts",
                )
            ],
        ]

        await query.edit_message_text(
            "⚙️ **Settings**\n\n" f"🔔 Notifications are now " f"{status_text}.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif query.data == "settings_back":
        await query.message.reply_text(
            "🏠 **Main Menu**\n\n" "Select an option from the menu below.",
            reply_markup=get_main_menu(),
            parse_mode="Markdown",
        )


async def handle_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "❌ Action cancelled.\n\n" "Returning to the main menu.",
        reply_markup=get_main_menu(),
    )


async def show_not_implemented(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🚧 This feature is coming soon!",
        reply_markup=get_main_menu(),
    )
