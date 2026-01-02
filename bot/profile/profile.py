from aiogram import F, Router
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.repositories.user_repository import ShopUserRepository
from backend.repositories.shop_page_repository import ShopPageRepository
from .keyboards import profile_kb

router = Router()

PAGE_PROFILE = "profile"  # ВАЖНО: совпадает с админкой


def _format_template(tpl: str, values: dict[str, object]) -> str:
    """
    Очень простой шаблонизатор для {key}.
    Не падает, если ключа нет — оставляет как есть.
    """
    if not tpl:
        return ""
    out = tpl
    for k, v in values.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def _build_profile_caption(
    page,
    *,
    fallback_title: str,
    fallback_body: str,
    values: dict[str, object],
) -> str:

    raw_title = page.title if page else fallback_title
    title = (raw_title or "").strip()

    raw_body = page.content if page else fallback_body
    body = (raw_body or "").strip()

    title = _format_template(title, values)
    body = _format_template(body, values)

    if title and body:
        return f"<b>{title}</b>\n\n{body}"
    if body:
        return body
    if title:
        return f"<b>{title}</b>"

    return ""


async def _render_profile(
    callback: CallbackQuery,
    *,
    shop_id: int,
    user_repo: ShopUserRepository,
    page_repo: ShopPageRepository,
    state: FSMContext,
):
    tg_id = callback.from_user.id
    user = await user_repo.get_user(shop_id=shop_id, tg_id=tg_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await state.clear()

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_PROFILE)

    values = {
        "user_id": user.tg_id,
        "orders_amount": user.orders_amount,
        "balance": user.balance,
        "username": (user.username or ""),
        "shop_id": shop_id,
    }

    fallback_title = "Профиль"
    fallback_body = (
        "Ваш ID профиля: <code>{user_id}</code>\n"
        "Количество заказов: {orders_amount} шт.\n"
        "Баланс: {balance} RUB"
    )

    caption = _build_profile_caption(
        page,
        fallback_title=fallback_title,
        fallback_body=fallback_body,
        values=values,
    )
    image = (page.image if page else None) or None

    if image:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=image, caption=caption, parse_mode="HTML"),
            reply_markup=profile_kb(),
        )
    else:
        await callback.message.edit_text(
            text=caption,
            parse_mode="HTML",
            reply_markup=profile_kb(),
        )

    await callback.answer()


@router.callback_query(F.data == "profile")
async def profile_clb(
    callback: CallbackQuery,
    state: FSMContext,
    shop_id: int,
    user_repo: ShopUserRepository,
    page_repo: ShopPageRepository,
):
    await _render_profile(
        callback,
        shop_id=shop_id,
        user_repo=user_repo,
        page_repo=page_repo,
        state=state,
    )
