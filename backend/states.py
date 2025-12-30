from aiogram.fsm.state import StatesGroup, State

class PromocodeStates(StatesGroup):
    waiting_for_code = State()

class PaymentStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment_system = State()

class CertificateStates(StatesGroup):
    waiting_fro_amount = State()

class BroadcastStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_text = State()
    waiting_for_buttons = State()
    waiting_for_button_title = State()
    choosing_button_target = State()
    waiting_for_confirmation = State()

class AdminShopStates(StatesGroup):
    choosing_action = State()
    choosing_category = State()
    choosing_subcategory = State()

    entering_category_name = State()
    entering_subcategory_name = State()
    entering_item_name = State()

    entering_item_price = State()
    entering_item_description = State()

    entering_category_img = State()
    entering_subcategory_img = State()
    entering_item_img = State()

class AdminUserBalanceStates(StatesGroup):
    waiting_for_amount = State()

class ReviewSG(StatesGroup):
    waiting_comment = State()

class SupportChatSG(StatesGroup):
    active = State()