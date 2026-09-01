from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from states import (
    FEE_ACADEMIC_SYSTEM,
    FEE_CREDIT_FEE,
    FEE_TRIMESTER_FEE,
    FEE_REG_CREDITS,
    FEE_RETAKE_COUNT,
    FEE_RETAKE_CREDITS,
    FEE_DISCOUNT_TYPE,
    FEE_DISCOUNT_PERCENT,
)

from keyboards import (
    get_main_menu,
    get_cancel_keyboard,
    get_fee_discount_keyboard,
)

from database import log_user_activity

INSTALLMENT_FINE = 500


def academic_system_keyboard():
    keyboard = [
        ["🔺 Trimester", "🟦 Semester"],
        ["❌ Cancel"],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


async def fee_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_user:
        log_user_activity(
            update.effective_user.id,
            update.effective_user.first_name,
            update.effective_user.username,
        )

    context.user_data["fee_data"] = {}

    await update.message.reply_text(
        "💰 Fee Calculator\n\n"
        "First, select your academic system.\n\n"
        "🔺 Trimester\n"
        "🟦 Semester",
        reply_markup=academic_system_keyboard(),
    )

    return FEE_ACADEMIC_SYSTEM


async def get_academic_system(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    if text == "🔺 Trimester":
        context.user_data["fee_data"]["academic_system"] = "Trimester"

    elif text == "🟦 Semester":
        context.user_data["fee_data"]["academic_system"] = "Semester"

    else:
        await update.message.reply_text(
            "Please select Trimester or Semester.",
            reply_markup=academic_system_keyboard(),
        )

        return FEE_ACADEMIC_SYSTEM

    await update.message.reply_text(
        "Step 2: Enter the Credit Fee per credit.\n\n" "Example: 6500",
        reply_markup=get_cancel_keyboard(),
    )

    return FEE_CREDIT_FEE


async def get_credit_fee(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        credit_fee = float(text)

        if credit_fee <= 0:
            raise ValueError

        context.user_data["fee_data"]["credit_fee"] = credit_fee

        await update.message.reply_text(
            "Step 3: Enter the " "Trimester/Semester Fee.\n\n" "Example: 5000",
            reply_markup=get_cancel_keyboard(),
        )

        return FEE_TRIMESTER_FEE

    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid positive number.")

        return FEE_CREDIT_FEE


async def get_trimester_fee(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        academic_fee = float(text)

        if academic_fee < 0:
            raise ValueError

        context.user_data["fee_data"]["trimester_fee"] = academic_fee

        await update.message.reply_text(
            "Step 4: Enter your total registered credits.\n\n" "Example: 15",
            reply_markup=get_cancel_keyboard(),
        )

        return FEE_REG_CREDITS

    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid number.")

        return FEE_TRIMESTER_FEE


async def get_reg_credits(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        credits = float(text)

        if credits <= 0:
            raise ValueError

        context.user_data["fee_data"]["reg_credits"] = credits

        data = context.user_data["fee_data"]

        data["retake_stage"] = "first"
        data["first_retake_count"] = 0
        data["first_retake_credits"] = []
        data["current_retake"] = 1

        await update.message.reply_text(
            "Step 5: How many FIRST-TIME retake courses "
            "do you have?\n\n"
            "First-time retake courses receive 50% discount.\n"
            "Enter 0 if you have none.",
            reply_markup=get_cancel_keyboard(),
        )

        return FEE_RETAKE_COUNT

    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid positive number.")

        return FEE_REG_CREDITS


async def get_retake_count(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        count = int(text)

        if count < 0:
            raise ValueError

        data = context.user_data["fee_data"]

        stage = data.get(
            "retake_stage",
            "first",
        )

        if stage == "first":

            data["first_retake_count"] = count
            data["first_retake_credits"] = []
            data["current_retake"] = 1

            if count > 0:
                await update.message.reply_text(
                    "Enter credit for FIRST-TIME " "Retake Course 1:",
                    reply_markup=get_cancel_keyboard(),
                )

                return FEE_RETAKE_CREDITS

            data["retake_stage"] = "repeat"
            data["repeat_retake_count"] = 0
            data["repeat_retake_credits"] = []
            data["current_retake"] = 1

            await update.message.reply_text(
                "Step 6: How many SECOND-TIME or "
                "SUBSEQUENT retake courses do you have?\n\n"
                "These retakes receive NO discount.\n"
                "They are NOT eligible for Scholarship or Tuition Waiver.\n\n"
                "Enter 0 if you have none.",
                reply_markup=get_cancel_keyboard(),
            )

            return FEE_RETAKE_COUNT

        data["repeat_retake_count"] = count
        data["repeat_retake_credits"] = []
        data["current_retake"] = 1

        if count > 0:
            await update.message.reply_text(
                "Enter credit for SECOND-TIME/" "SUBSEQUENT Retake Course 1:",
                reply_markup=get_cancel_keyboard(),
            )

            return FEE_RETAKE_CREDITS

        await update.message.reply_text(
            "Step 7: Do you have a Scholarship "
            "or Tuition Waiver?\n\n"
            "⚠️ Scholarship/Waiver applies only "
            "to regular course tuition.\n"
            "⚠️ Retake courses are not eligible.",
            reply_markup=get_fee_discount_keyboard(),
        )

        return FEE_DISCOUNT_TYPE

    except ValueError:
        await update.message.reply_text("⚠️ Please enter 0 or a positive whole number.")

        return FEE_RETAKE_COUNT


async def get_retake_credits(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        credit = float(text)

        if credit <= 0:
            raise ValueError

        data = context.user_data["fee_data"]

        stage = data.get(
            "retake_stage",
            "first",
        )

        if stage == "first":

            data["first_retake_credits"].append(credit)

            current = data["current_retake"]
            total = data["first_retake_count"]

            if current < total:

                data["current_retake"] += 1

                await update.message.reply_text(
                    f"Enter credit for FIRST-TIME " f"Retake Course {current + 1}:",
                    reply_markup=get_cancel_keyboard(),
                )

                return FEE_RETAKE_CREDITS

            data["retake_stage"] = "repeat"
            data["repeat_retake_count"] = 0
            data["repeat_retake_credits"] = []
            data["current_retake"] = 1

            await update.message.reply_text(
                "Step 6: How many SECOND-TIME or "
                "SUBSEQUENT retake courses do you have?\n\n"
                "These retakes receive NO discount.\n"
                "They are NOT eligible for Scholarship "
                "or Tuition Waiver.\n\n"
                "Enter 0 if you have none.",
                reply_markup=get_cancel_keyboard(),
            )

            return FEE_RETAKE_COUNT

        data["repeat_retake_credits"].append(credit)

        current = data["current_retake"]
        total = data["repeat_retake_count"]

        if current < total:

            data["current_retake"] += 1

            await update.message.reply_text(
                f"Enter credit for SECOND-TIME/"
                f"SUBSEQUENT Retake Course {current + 1}:",
                reply_markup=get_cancel_keyboard(),
            )

            return FEE_RETAKE_CREDITS

        await update.message.reply_text(
            "Step 7: Do you have a Scholarship "
            "or Tuition Waiver?\n\n"
            "⚠️ Scholarship/Waiver applies only "
            "to regular course tuition.\n"
            "⚠️ Retake courses are not eligible.",
            reply_markup=get_fee_discount_keyboard(),
        )

        return FEE_DISCOUNT_TYPE

    except ValueError:
        await update.message.reply_text(
            "⚠️ Please enter a valid positive credit number."
        )

        return FEE_RETAKE_CREDITS


async def get_discount_type(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    choice = update.message.text.strip()

    if choice == "⏩ None":

        context.user_data["fee_data"]["discount_type"] = "None"

        context.user_data["fee_data"]["discount_percent"] = 0

        return await calculate_fees(
            update,
            context,
        )

    if choice in [
        "🎁 Scholarship",
        "💸 Tuition Waiver",
    ]:

        context.user_data["fee_data"]["discount_type"] = choice

        await update.message.reply_text(
            "Enter the discount percentage.\n\n" "Example: 25",
            reply_markup=get_cancel_keyboard(),
        )

        return FEE_DISCOUNT_PERCENT

    await update.message.reply_text(
        "Please choose an option from the keyboard.",
        reply_markup=get_fee_discount_keyboard(),
    )

    return FEE_DISCOUNT_TYPE


async def get_discount_percent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        percent = float(text)

        if percent < 0 or percent > 100:
            raise ValueError

        context.user_data["fee_data"]["discount_percent"] = percent

        return await calculate_fees(
            update,
            context,
        )

    except ValueError:
        await update.message.reply_text("⚠️ Enter a percentage between 0 and 100.")

        return FEE_DISCOUNT_PERCENT


async def calculate_fees(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    data = context.user_data["fee_data"]

    academic_system = data["academic_system"]

    credit_fee = data["credit_fee"]

    academic_fee = data["trimester_fee"]

    reg_credits = data.get(
        "reg_credits",
        0,
    )

    first_retake_credits = sum(
        data.get(
            "first_retake_credits",
            [],
        )
    )

    repeat_retake_credits = sum(
        data.get(
            "repeat_retake_credits",
            [],
        )
    )

    total_retake_credits = first_retake_credits + repeat_retake_credits

    regular_credits = reg_credits - total_retake_credits

    if regular_credits < 0:
        regular_credits = 0

    regular_tuition = regular_credits * credit_fee

    first_retake_normal = first_retake_credits * credit_fee

    first_retake_discount = first_retake_normal * 0.50

    first_retake_tuition = first_retake_normal - first_retake_discount

    repeat_retake_tuition = repeat_retake_credits * credit_fee

    discount_type = data.get(
        "discount_type",
        "None",
    )

    discount_percent = data.get(
        "discount_percent",
        0,
    )

    regular_discount = regular_tuition * discount_percent / 100

    final_regular_tuition = regular_tuition - regular_discount

    other_fees = getattr(
        __import__("config").Config,
        "DEFAULT_OTHER_FEES",
        0,
    )

    total_tuition = final_regular_tuition + first_retake_tuition + repeat_retake_tuition

    total_discount = first_retake_discount + regular_discount

    total_payable = total_tuition + academic_fee + other_fees

    if academic_system == "Trimester":

        installment_percentages = [
            40,
            30,
            30,
        ]

    else:

        installment_percentages = [
            25,
            25,
            25,
            25,
        ]

    installment_lines = []

    for index, percentage in enumerate(
        installment_percentages,
        start=1,
    ):
        amount = total_payable * percentage / 100

        installment_lines.append(
            f"{index}️⃣ Installment: " f"{percentage}% → " f"{amount:,.2f} BDT"
        )

    installment_text = "\n".join(installment_lines)

    result = (
        "💰 FEE CALCULATION\n\n"
        f"Academic System: {academic_system}\n"
        f"Credit Fee: {credit_fee:,.2f} BDT\n"
        f"{academic_system} Fee: "
        f"{academic_fee:,.2f} BDT\n\n"
        f"Registered Credits: "
        f"{reg_credits:,.2f}\n"
        f"Regular Credits: "
        f"{regular_credits:,.2f}\n"
        f"First-Time Retake Credits: "
        f"{first_retake_credits:,.2f}\n"
        f"Subsequent Retake Credits: "
        f"{repeat_retake_credits:,.2f}\n\n"
        f"Regular Tuition: "
        f"{regular_tuition:,.2f} BDT\n"
        f"First-Time Retake Tuition: "
        f"{first_retake_tuition:,.2f} BDT\n"
        f"Subsequent Retake Tuition: "
        f"{repeat_retake_tuition:,.2f} BDT\n\n"
        f"First-Time Retake Discount (50%): "
        f"-{first_retake_discount:,.2f} BDT\n"
        f"{discount_type} Discount on Regular Tuition: "
        f"-{regular_discount:,.2f} BDT\n"
        f"Total Discount: "
        f"-{total_discount:,.2f} BDT\n\n"
        f"Other Fees: "
        f"{other_fees:,.2f} BDT\n"
        f"💵 TOTAL PAYABLE: "
        f"{total_payable:,.2f} BDT\n\n"
        f"📅 {academic_system.upper()} INSTALLMENT PLAN\n\n"
        f"{installment_text}\n\n"
        "⚠️ PAYMENT FAILURE POLICY\n"
        f"If an installment payment fails, "
        f"a fine of {INSTALLMENT_FINE:,.0f} BDT "
        "will be applicable.\n\n"
        "ℹ️ First-time retake gets 50% discount.\n"
        "ℹ️ Subsequent retakes get no discount.\n"
        "ℹ️ Retake courses are not eligible for "
        "Scholarship or Tuition Waiver."
    )

    context.user_data.pop(
        "fee_data",
        None,
    )

    await update.message.reply_text(
        result,
        reply_markup=get_main_menu(),
    )

    return ConversationHandler.END


async def fee_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.pop(
        "fee_data",
        None,
    )

    await update.message.reply_text(
        "❌ Fee calculation cancelled.",
        reply_markup=get_main_menu(),
    )

    return ConversationHandler.END
