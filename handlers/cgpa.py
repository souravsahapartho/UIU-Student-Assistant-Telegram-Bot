from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from states import (
    CGPA_PREV_CREDITS,
    CGPA_PREV_CGPA,
    CGPA_COURSE_COUNT,
    CGPA_COURSE_CREDIT,
    CGPA_COURSE_GRADE,
)

from keyboards import (
    get_main_menu,
    get_grade_keyboard,
)

from database import log_user_activity

GRADE_POINTS = {
    "A": 4.00,
    "A-": 3.67,
    "B+": 3.33,
    "B": 3.00,
    "B-": 2.67,
    "C+": 2.33,
    "C": 2.00,
    "C-": 1.67,
    "D+": 1.33,
    "D": 1.00,
    "F": 0.00,
}

NON_GPA_GRADES = {
    "I",
    "W",
    "R",
}


def get_cgpa_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["📚 Grading System"],
            ["❌ Cancel"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
    )


def get_grading_system_text():
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


def get_current_step_text(context):
    current_step = context.user_data.get(
        "cgpa_current_step",
        "prev_credits",
    )

    data = context.user_data.get(
        "cgpa_data",
        {},
    )

    if current_step == "prev_credits":
        return (
            "Step 1: Enter your previously completed credits.\n\n"
            "Example: <code>45</code>\n\n"
            "If you are in your first semester, enter <code>0</code>."
        )

    if current_step == "prev_cgpa":
        return "Step 2: Enter your current CGPA.\n\n" "Example: <code>3.42</code>"

    if current_step == "course_count":
        return "Step 3: How many courses are you taking this semester?"

    if current_step == "course_credit":
        course_number = data.get(
            "current_course",
            1,
        )

        return (
            f"Course {course_number}:\n\n"
            f"Enter the credit for Course {course_number}.\n\n"
            "Example: <code>3</code>"
        )

    if current_step == "course_grade":
        course_number = data.get(
            "current_course",
            1,
        )

        return f"Course {course_number}:\n\n" "Select the grade:"

    return (
        "Step 1: Enter your previously completed credits.\n\n"
        "Example: <code>45</code>"
    )


async def cgpa_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_user:
        log_user_activity(
            update.effective_user.id,
            update.effective_user.first_name,
            update.effective_user.username,
        )

    context.user_data.pop(
        "cgpa_data",
        None,
    )

    context.user_data["cgpa_data"] = {
        "courses": [],
        "current_course": 1,
    }

    context.user_data["cgpa_current_step"] = "prev_credits"

    await update.message.reply_text(
        "🎓 <b>CGPA Calculator</b>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML",
    )

    await update.message.reply_text(
        get_current_step_text(context),
        reply_markup=get_cgpa_keyboard(),
        parse_mode="HTML",
    )

    return CGPA_PREV_CREDITS


async def cgpa_grading_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        get_grading_system_text(),
        parse_mode="HTML",
        reply_markup=get_cgpa_keyboard(),
    )

    await update.message.reply_text(
        get_current_step_text(context),
        reply_markup=(
            get_cgpa_keyboard()
            if context.user_data.get("cgpa_current_step") != "course_grade"
            else get_grade_keyboard()
        ),
        parse_mode="HTML",
    )

    current_step = context.user_data.get(
        "cgpa_current_step",
        "prev_credits",
    )

    if current_step == "prev_credits":
        return CGPA_PREV_CREDITS

    if current_step == "prev_cgpa":
        return CGPA_PREV_CGPA

    if current_step == "course_count":
        return CGPA_COURSE_COUNT

    if current_step == "course_credit":
        return CGPA_COURSE_CREDIT

    if current_step == "course_grade":
        return CGPA_COURSE_GRADE

    return CGPA_PREV_CREDITS


async def get_prev_credits(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        credits = float(text)

        if credits < 0:
            raise ValueError

        context.user_data["cgpa_data"]["prev_credits"] = credits

    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid input.\n\n" "Please enter a valid number.\n\n" "Example: 45",
            reply_markup=get_cgpa_keyboard(),
        )
        return CGPA_PREV_CREDITS

    if credits == 0:
        context.user_data["cgpa_data"]["prev_cgpa"] = 0.0
        context.user_data["cgpa_current_step"] = "course_count"

        await update.message.reply_text(
            "Step 2: How many courses are you taking this semester?",
            reply_markup=get_cgpa_keyboard(),
        )

        return CGPA_COURSE_COUNT

    context.user_data["cgpa_current_step"] = "prev_cgpa"

    await update.message.reply_text(
        "Step 2: Enter your current CGPA.\n\n" "Example: <code>3.42</code>",
        reply_markup=get_cgpa_keyboard(),
        parse_mode="HTML",
    )

    return CGPA_PREV_CGPA


async def get_prev_cgpa(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        cgpa = float(text)

        if cgpa < 0 or cgpa > 4.00:
            raise ValueError

        context.user_data["cgpa_data"]["prev_cgpa"] = cgpa

    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid CGPA.\n\n"
            "Please enter a value between 0.00 and 4.00.\n\n"
            "Example: 3.42",
            reply_markup=get_cgpa_keyboard(),
        )
        return CGPA_PREV_CGPA

    context.user_data["cgpa_current_step"] = "course_count"

    await update.message.reply_text(
        "Step 3: How many courses are you taking this semester?",
        reply_markup=get_cgpa_keyboard(),
    )

    return CGPA_COURSE_COUNT


async def get_course_count(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        count = int(text)

        if count < 1 or count > 30:
            raise ValueError

        context.user_data["cgpa_data"]["course_count"] = count
        context.user_data["cgpa_data"]["current_course"] = 1
        context.user_data["cgpa_data"]["courses"] = []

        context.user_data["cgpa_current_step"] = "course_credit"

    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid number of courses.\n\n"
            "Please enter a number between 1 and 30.",
            reply_markup=get_cgpa_keyboard(),
        )
        return CGPA_COURSE_COUNT

    await update.message.reply_text(
        "Course 1:\n\n" "Enter the credit for Course 1.\n\n" "Example: <code>3</code>",
        reply_markup=get_cgpa_keyboard(),
        parse_mode="HTML",
    )

    return CGPA_COURSE_CREDIT


async def get_course_credit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        credit = float(text)

        if credit <= 0 or credit > 20:
            raise ValueError

        context.user_data["cgpa_data"]["temp_credit"] = credit
        context.user_data["cgpa_current_step"] = "course_grade"

    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid credit.\n\n"
            "Please enter a valid positive number.\n\n"
            "Example: 3",
            reply_markup=get_cgpa_keyboard(),
        )
        return CGPA_COURSE_CREDIT

    course_number = context.user_data["cgpa_data"]["current_course"]

    await update.message.reply_text(
        f"Course {course_number}:\n\n" "Select the grade:",
        reply_markup=get_grade_keyboard(),
    )

    return CGPA_COURSE_GRADE


async def get_course_grade(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    grade = update.message.text.strip().upper()

    if grade not in GRADE_POINTS and grade not in NON_GPA_GRADES:
        await update.message.reply_text(
            "⚠️ Invalid grade.\n\n" "Please select a valid grade.",
            reply_markup=get_grade_keyboard(),
        )

        return CGPA_COURSE_GRADE

    data = context.user_data["cgpa_data"]

    credit = data["temp_credit"]
    current_course = data["current_course"]
    course_count = data["course_count"]

    data["courses"].append(
        {
            "course": current_course,
            "credit": credit,
            "grade": grade,
        }
    )

    data.pop(
        "temp_credit",
        None,
    )

    if current_course < course_count:
        next_course = current_course + 1

        data["current_course"] = next_course
        context.user_data["cgpa_current_step"] = "course_credit"

        await update.message.reply_text(
            f"Course {next_course}:\n\n"
            f"Enter the credit for Course {next_course}.\n\n"
            "Example: <code>3</code>",
            reply_markup=get_cgpa_keyboard(),
            parse_mode="HTML",
        )

        return CGPA_COURSE_CREDIT

    return await calculate_final_cgpa(
        update,
        context,
    )


async def cgpa_new_calc(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    return await cgpa_start(
        update,
        context,
    )


async def calculate_final_cgpa(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    data = context.user_data["cgpa_data"]

    previous_credits = float(
        data.get(
            "prev_credits",
            0.0,
        )
    )

    previous_cgpa = float(
        data.get(
            "prev_cgpa",
            0.0,
        )
    )

    courses = data.get(
        "courses",
        [],
    )

    semester_credits = 0.0
    semester_quality_points = 0.0

    for course in courses:
        credit = float(course["credit"])

        grade = course["grade"]

        if grade in NON_GPA_GRADES:
            continue

        grade_point = GRADE_POINTS.get(
            grade,
            0.0,
        )

        semester_credits += credit
        semester_quality_points += credit * grade_point

    if semester_credits > 0:
        semester_gpa = semester_quality_points / semester_credits
    else:
        semester_gpa = 0.0

    previous_quality_points = previous_credits * previous_cgpa

    total_quality_points = previous_quality_points + semester_quality_points

    total_credits = previous_credits + semester_credits

    if total_credits > 0:
        updated_cgpa = total_quality_points / total_credits
    else:
        updated_cgpa = 0.0

    result = (
        "🎓 <b>CGPA Calculation Result</b>\n\n"
        f"📊 Previous Credits: {previous_credits:.2f}\n"
        f"📈 Previous CGPA: {previous_cgpa:.2f}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📚 Semester Credits: {semester_credits:.2f}\n"
        f"🎯 Semester GPA: {semester_gpa:.2f}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Total Credits: {total_credits:.2f}\n"
        f"🎓 <b>Updated CGPA: {updated_cgpa:.2f}</b>\n\n"
        "ℹ️ I, W and R grades are excluded from GPA calculation."
    )

    context.user_data.pop(
        "cgpa_data",
        None,
    )

    context.user_data.pop(
        "cgpa_current_step",
        None,
    )

    await update.message.reply_text(
        result,
        reply_markup=get_main_menu(),
        parse_mode="HTML",
    )

    return ConversationHandler.END


async def cgpa_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.pop(
        "cgpa_data",
        None,
    )

    context.user_data.pop(
        "cgpa_current_step",
        None,
    )

    await update.message.reply_text(
        "❌ CGPA calculation cancelled.",
        reply_markup=get_main_menu(),
    )

    return ConversationHandler.END
