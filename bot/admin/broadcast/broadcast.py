from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.states import BroadcastStates
from backend.repositories.user_repository import ShopUserRepository
from backend.repositories.shop_repository import ShopRepository

from .keyboards import build_broadcast_bt, build_items_cat_kb, broadcast_kb, cancell_broadcast_kb

router = Router()


@router.callback_query(F.data == "admin_broadcast")
async def cmd_send(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Отправьте картинку для рассылки:",
        reply_markup=cancell_broadcast_kb()
        )
    await state.set_state(BroadcastStates.waiting_for_photo)


@router.message(F.photo, BroadcastStates.waiting_for_photo)
async def process_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await message.answer(
        text="Отправьте текст рассылки (поддерживаются HTML теги):",
        reply_markup=cancell_broadcast_kb()
        )
    await state.set_state(BroadcastStates.waiting_for_text)


@router.message(BroadcastStates.waiting_for_text)
async def process_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    data = await state.get_data()

    try:
        await message.answer_photo(photo=data['photo'], caption=data['text'])
    except TelegramBadRequest:
        await message.answer(
            text="Ошибка в HTML тегах. Проверьте теги и пересоздайте рассылку",
            reply_markup=cancell_broadcast_kb()
            )
        return

    await message.answer(
        text="Хотите добавить кнопки?", 
        reply_markup=build_broadcast_bt()
        )
    await state.set_state(BroadcastStates.waiting_for_buttons)


@router.callback_query(F.data == "broadcast_add_button", BroadcastStates.waiting_for_buttons)
async def ask_button_title(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Введите название кнопки:",
        reply_markup=cancell_broadcast_kb()
        )
    await state.set_state(BroadcastStates.waiting_for_button_title)


@router.message(BroadcastStates.waiting_for_button_title)
async def save_button_title(message: Message, state: FSMContext):
    await state.update_data(current_button_title=message.text)

    kb = InlineKeyboardBuilder()
    kb.button(text="Категория", callback_data="btn_target_category")
    kb.button(text="Подкатегория", callback_data="btn_target_subcategory")
    kb.button(text="Товар", callback_data="btn_target_item")
    kb.adjust(1)

    await message.answer("К чему привязать кнопку?", reply_markup=kb.as_markup())
    await state.set_state(BroadcastStates.choosing_button_target)



@router.callback_query(F.data.startswith("btn_target_"), BroadcastStates.choosing_button_target)
async def choose_target(callback: CallbackQuery, state: FSMContext, shop_repo: ShopRepository):
    target_type = callback.data.split("_")[-1]

    if target_type == "category":
        items = await shop_repo.get_categories()
    elif target_type == "subcategory":
        items = await shop_repo.get_subcategories()
    elif target_type == "item":
        items = await shop_repo.get_items()
    else:
        await callback.answer("Неверный тип цели", show_alert=True)
        return

    await callback.message.edit_text(
        text="Выберите к чему привязать кнопку:", 
        reply_markup=build_items_cat_kb(items, target_type, page=0)
    )
    await state.update_data({
        "target_type": target_type,
        "items": items
    })
    
@router.callback_query(F.data.startswith("paginate:"), BroadcastStates.choosing_button_target)
async def paginate_items(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Некорректные данные пагинации", show_alert=True)
        return
    
    _, target_type, page = parts
    page = int(page)

    data = await state.get_data()
    items = data.get("items", [])

    kb = build_items_cat_kb(items, target_type, page)
    await callback.message.edit_reply_markup(reply_markup=kb)

@router.callback_query(F.data.startswith("btn:"), BroadcastStates.choosing_button_target)
async def add_button(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("Некорректные данные кнопки", show_alert=True)
        return

    _, target_type, target_id, _ = parts
    target_id = int(target_id)

    data = await state.get_data()
    button_title = data.get("current_button_title", "Кнопка")

    buttons = data.get("buttons", [])
    buttons.append({
        "text": button_title,
        "target_type": target_type,
        "target_id": target_id
    })
    await state.update_data(buttons=buttons, current_button_title=None)

    await callback.message.answer(
        f"Кнопка <b>{button_title}</b> добавлена ✅",
        parse_mode="HTML"
    )

    await callback.message.answer(
        text="Хотите добавить ещё кнопки?",
        reply_markup=build_broadcast_bt()
    )
    await state.set_state(BroadcastStates.waiting_for_buttons)


@router.callback_query(F.data == "broadcast_skip_buttons", BroadcastStates.waiting_for_buttons)
async def skip_buttons(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    kb = None
    if "buttons" in data and data["buttons"]:
        builder = InlineKeyboardBuilder()
        for btn in data["buttons"]:
            builder.button(
                text=btn["text"],
                callback_data=f"{btn['target_type']}:{btn['target_id']}"
            )
        builder.adjust(1)
        kb = builder.as_markup()

    try:
        await callback.message.answer_photo(photo=data['photo'], caption=data['text'], reply_markup=kb)
    except TelegramBadRequest:
        await callback.message.answer("Ошибка в HTML тегах. Проверьте теги.")
        return

    await callback.message.answer(
        text="Подтверждаете рассылку?", 
        reply_markup=broadcast_kb()
        )
    await state.set_state(BroadcastStates.waiting_for_confirmation)


@router.callback_query(F.data == "broadcast_confirm", BroadcastStates.waiting_for_confirmation)
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext, user_repo: ShopUserRepository):
    await callback.message.edit_reply_markup(None)
    data = await state.get_data()
    photo_id = data['photo']
    text = data['text']

    kb = None
    if "buttons" in data and data["buttons"]:
        builder = InlineKeyboardBuilder()
        for btn in data["buttons"]:
            builder.button(
                text=btn["text"],
                callback_data=f"{btn['target_type']}:{btn['target_id']}"
            )
        builder.adjust(1)
        kb = builder.as_markup()

    await callback.message.answer("Начинаю рассылку...")
    await user_repo.broadcast_message(callback.bot, photo_id, text, reply_markup=kb)

    await callback.message.answer("Рассылка завершена!")
    await state.clear()


@router.callback_query(F.data == "broadcast_cancel", BroadcastStates.waiting_for_confirmation)
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Рассылка отменена.")
    await state.clear()
