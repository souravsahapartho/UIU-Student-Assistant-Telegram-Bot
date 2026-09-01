from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from database import get_setting, update_setting, get_all_users


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in Config.ADMIN_USER_IDS:
        await update.message.reply_text(
            "❌ You are not authorized to access the admin panel."
        )
        return

    args = context.args

    if not args:
        await update.message.reply_text(
            "🛠 Admin Commands\n\n"
            "/admin view\n"
            "/admin set KEY VALUE\n"
            "/admin broadcast MESSAGE"
        )
        return

    command = args[0].lower()

    if command == "view":
        c_fee = get_setting(
            "CREDIT_FEE",
            Config.DEFAULT_CREDIT_FEE,
        )

        t_fee = get_setting(
            "TRIMESTER_FEE",
            Config.DEFAULT_TRIMESTER_FEE,
        )

        min_p = get_setting(
            "MINIMUM_PAYMENT",
            Config.DEFAULT_MINIMUM_PAYMENT,
        )

        msg = (
            "⚙️ Current Settings\n\n"
            f"CREDIT_FEE = {c_fee}\n"
            f"TRIMESTER_FEE = {t_fee}\n"
            f"MINIMUM_PAYMENT = {min_p}"
        )

        await update.message.reply_text(msg)
        return

    if command == "set" and len(args) == 3:
        key = args[1].upper()
        value = args[2]

        try:
            val_float = float(value)
            update_setting(key, val_float)

            await update.message.reply_text(
                f"✅ Successfully updated {key} to {val_float}"
            )

        except ValueError:
            await update.message.reply_text("❌ Value must be a number.")

        return

    if command == "broadcast":
        if len(args) < 2:
            await update.message.reply_text("❌ Usage:\n/admin broadcast Your message")
            return

        message = " ".join(args[1:])
        await broadcast_message(update, context, message)
        return

    await update.message.reply_text("❌ Invalid admin command.")


async def admin_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.message.from_user.id

    if user_id not in Config.ADMIN_USER_IDS:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if not context.args:
        await update.message.reply_text("❌ Usage:\n/admin broadcast Your message")
        return

    message = " ".join(context.args)

    await broadcast_message(
        update,
        context,
        message,
    )


async def broadcast_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: str,
):
    users = get_all_users()

    success = 0
    failed = 0

    for user in users:
        try:
            telegram_id = user["telegram_id"] if isinstance(user, dict) else user
            await context.bot.send_message(
                chat_id=telegram_id,
                text=message,
            )
            success += 1

        except Exception:
            failed += 1

    await update.message.reply_text(
        "📢 Broadcast completed.\n\n" f"✅ Sent: {success}\n" f"❌ Failed: {failed}"
    )
