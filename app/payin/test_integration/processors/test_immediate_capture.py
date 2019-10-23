from typing import List

import pytest

from app.payin.core.cart_payment.processor import CartPaymentProcessor
from app.payin.core.cart_payment.types import IntentStatus, LegacyStripeChargeStatus
from app.payin.core.payer.model import Payer
from app.payin.core.payment_method.model import PaymentMethod
from app.payin.repository.cart_payment_repo import CartPaymentRepository
from app.payin.test_integration.processors.capture_payment_intent_test_base import (
    CapturePaymentIntentLegacyTest,
    CapturePaymentIntentTest,
    CartPaymentState,
    PaymentIntentState,
    PgpPaymentIntentState,
    StripeChargeState,
)

create_no_adjust_test_data = [
    CartPaymentState(
        description="create cart payment with 1000 amount",
        initial_amount=1000,
        amount_delta_update=None,
        expected_amount=1000,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=1000,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    )
]
create_and_partial_refund_test_data = [
    CartPaymentState(
        description="create cart payment with 1000 amount",
        initial_amount=1000,
        amount_delta_update=None,
        expected_amount=1000,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=1000,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="[partial refund] adjust cart payment with -500 amount",
        initial_amount=1000,
        amount_delta_update=-500,
        expected_amount=500,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=500,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=500,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
]

create_and_full_refund_test_data = [
    CartPaymentState(
        description="create cart payment with 1000 amount",
        initial_amount=1000,
        amount_delta_update=None,
        expected_amount=1000,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=1000,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="[full refund] adjust cart payment with -1000 amount",
        initial_amount=1000,
        amount_delta_update=-1000,
        expected_amount=0,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=0,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=1000,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
]

create_and_partial_refund_and_full_refund_test_data = [
    CartPaymentState(
        description="create cart payment with 1000 amount",
        initial_amount=1000,
        amount_delta_update=None,
        expected_amount=1000,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=1000,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="[partial refund] adjust cart payment with -200 amount",
        initial_amount=1000,
        amount_delta_update=-200,
        expected_amount=800,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=800,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=200,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="[full refund] adjust cart payment with -800 amount",
        initial_amount=1000,
        amount_delta_update=-800,
        expected_amount=0,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=0,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=1000,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
]

create_and_partial_refund_and_adjust_to_no_exceed_original_test_data = [
    CartPaymentState(
        description="create cart payment with 1000 amount",
        initial_amount=1000,
        amount_delta_update=None,
        expected_amount=1000,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=1000,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="[partial refund] adjust cart payment with -200 amount",
        initial_amount=1000,
        amount_delta_update=-200,
        expected_amount=800,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=800,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=200,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="adjust cart payment with +50 amount",
        initial_amount=1000,
        amount_delta_update=50,
        expected_amount=850,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=0,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=1000,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
            PaymentIntentState(
                amount=850,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=850,
                    amount_capturable=0,
                    amount_received=850,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=850,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
        ],
    ),
]

create_and_partial_refund_and_adjust_to_exceed_original_test_data = [
    CartPaymentState(
        description="create cart payment with 1000 amount",
        initial_amount=1000,
        amount_delta_update=None,
        expected_amount=1000,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=1000,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="[partial refund] cart payment with -200 amount",
        initial_amount=1000,
        amount_delta_update=-200,
        expected_amount=800,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=800,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=200,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="adjust cart payment with +300 amount",
        initial_amount=1000,
        amount_delta_update=300,
        expected_amount=1100,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=0,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=1000,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
            PaymentIntentState(
                amount=1100,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1100,
                    amount_capturable=0,
                    amount_received=1100,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1100,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
        ],
    ),
]

create_and_adjust_to_exceed_original_test_data = [
    CartPaymentState(
        description="create cart payment with 1000 amount",
        initial_amount=1000,
        amount_delta_update=None,
        expected_amount=1000,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=1000,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="adjust cart payment with +300 amount",
        initial_amount=1000,
        amount_delta_update=300,
        expected_amount=1300,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=0,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=1000,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
            PaymentIntentState(
                amount=1300,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1300,
                    amount_capturable=0,
                    amount_received=1300,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1300,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
        ],
    ),
]

create_and_adjust_to_exceed_original_and_full_refund_test_data = [
    CartPaymentState(
        description="create cart payment with 1000 amount",
        initial_amount=1000,
        amount_delta_update=None,
        expected_amount=1000,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=1000,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="adjust cart payment with +300 amount",
        initial_amount=1000,
        amount_delta_update=300,
        expected_amount=1300,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=0,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=1000,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
            PaymentIntentState(
                amount=1300,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1300,
                    amount_capturable=0,
                    amount_received=1300,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1300,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
        ],
    ),
    CartPaymentState(
        description="[full refund] cart payment with -1300 amount",
        initial_amount=1000,
        amount_delta_update=-1300,
        expected_amount=0,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=0,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=1000,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
            PaymentIntentState(
                amount=0,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1300,
                    amount_capturable=0,
                    amount_received=1300,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1300,
                    amount_refunded=1300,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
        ],
    ),
]

create_and_adjust_to_exceed_original_and_partial_refund_test_data = [
    CartPaymentState(
        description="create cart payment with 1000 amount",
        initial_amount=1000,
        amount_delta_update=None,
        expected_amount=1000,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=1000,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="adjust cart payment with +300 amount",
        initial_amount=1000,
        amount_delta_update=300,
        expected_amount=1300,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=0,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=1000,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
            PaymentIntentState(
                amount=1300,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1300,
                    amount_capturable=0,
                    amount_received=1300,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1300,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
        ],
    ),
    CartPaymentState(
        description="adjust cart payment with -300 amount",
        initial_amount=1000,
        amount_delta_update=-300,
        expected_amount=1000,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=0,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=1000,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
            PaymentIntentState(
                amount=1000,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1300,
                    amount_capturable=0,
                    amount_received=1300,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1300,
                    amount_refunded=300,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            ),
        ],
    ),
]

create_and_partial_refund_and_partial_refund_test_data = [
    CartPaymentState(
        description="create cart payment with 1000 amount",
        initial_amount=1000,
        amount_delta_update=None,
        expected_amount=1000,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=1000,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=0,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="[partial refund] adjust cart payment with -200 amount",
        initial_amount=1000,
        amount_delta_update=-200,
        expected_amount=800,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=800,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=200,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
    CartPaymentState(
        description="[partial refund] cart payment with -200 amount",
        initial_amount=1000,
        amount_delta_update=-200,
        expected_amount=600,
        capture_intents=False,
        delay_capture=False,
        payment_intent_states=[
            PaymentIntentState(
                amount=600,
                status=IntentStatus.SUCCEEDED,
                pgp_payment_intent_state=PgpPaymentIntentState(
                    amount=1000,
                    amount_capturable=0,
                    amount_received=1000,
                    status=IntentStatus.SUCCEEDED,
                ),
                stripe_charge_state=StripeChargeState(
                    amount=1000,
                    amount_refunded=400,
                    status=LegacyStripeChargeStatus.SUCCEEDED,
                ),
            )
        ],
    ),
]

cart_payment_immediate_capture_state_transit_tests = [
    pytest.param(create_no_adjust_test_data, id="create_no_adjust"),
    pytest.param(create_and_partial_refund_test_data, id="create_and_partial_refund"),
    pytest.param(create_and_full_refund_test_data, id="create_and_full_refund"),
    pytest.param(
        create_and_partial_refund_and_full_refund_test_data,
        id="create_and_partial_refund_and_full_refund",
    ),
    pytest.param(
        create_and_partial_refund_and_partial_refund_test_data,
        id="create_and_partial_refund_and_partial_refund_test_data",
    ),
    pytest.param(
        create_and_partial_refund_and_adjust_to_no_exceed_original_test_data,
        id="create_and_partial_refund_and_adjust_to_no_exceed_original",
    ),
    pytest.param(
        create_and_partial_refund_and_adjust_to_exceed_original_test_data,
        id="create_and_partial_refund_and_adjust_to_exceed_original",
    ),
    pytest.param(
        create_and_adjust_to_exceed_original_test_data,
        id="create_and_adjust_to_exceed_original",
    ),
    pytest.param(
        create_and_adjust_to_exceed_original_and_partial_refund_test_data,
        id="create_and_adjust_to_exceed_original_and_partial_refund",
    ),
    pytest.param(
        create_and_adjust_to_exceed_original_and_full_refund_test_data,
        id="create_and_adjust_to_exceed_original_and_full_refund",
    ),
]


class TestImmediateCapturePaymentIntent(CapturePaymentIntentTest):
    pytestmark = [pytest.mark.asyncio, pytest.mark.external]

    @pytest.mark.parametrize(
        "cart_payment_states", cart_payment_immediate_capture_state_transit_tests
    )
    async def test_cart_payment_state_transit(
        self,
        cart_payment_states: List[CartPaymentState],
        cart_payment_processor: CartPaymentProcessor,
        cart_payment_repository: CartPaymentRepository,
        payer: Payer,
        payment_method: PaymentMethod,
    ):
        await super()._test_cart_payment_state_transition(
            cart_payment_states,
            cart_payment_processor,
            cart_payment_repository,
            payer,
            payment_method,
        )


class TestImmediateCapturePaymentIntentLegacy(CapturePaymentIntentLegacyTest):
    pytestmark = [pytest.mark.asyncio, pytest.mark.external]

    @pytest.mark.parametrize(
        "cart_payment_states", cart_payment_immediate_capture_state_transit_tests
    )
    async def test_cart_payment_state_transit(
        self,
        cart_payment_states: List[CartPaymentState],
        cart_payment_processor: CartPaymentProcessor,
        cart_payment_repository: CartPaymentRepository,
        payer: Payer,
        payment_method: PaymentMethod,
    ):
        await super()._test_cart_payment_state_transition(
            cart_payment_states,
            cart_payment_processor,
            cart_payment_repository,
            payer,
            payment_method,
        )
