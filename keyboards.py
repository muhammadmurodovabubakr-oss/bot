from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_search_results_keyboard(results: list) -> InlineKeyboardMarkup:
    """
    Qidiruv natijalari uchun 1, 2, 3... tugmalarini yaratadi.
    """
    buttons = []
    row = []
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, item in enumerate(results):
        label = emojis[i] if i < len(emojis) else str(i + 1)
        row.append(InlineKeyboardButton(text=label, callback_data=f"dl:{item['id']}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)
