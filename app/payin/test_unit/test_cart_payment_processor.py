import uuid
from unittest.mock import MagicMock

import pytest

import app.payin.core.cart_payment.processor as processor
from app.commons.types import CountryCode, Currency
from app.payin.core.cart_payment.model import CartPayment, IntentStatus, SplitPayment
from app.payin.core.cart_payment.types import LegacyStripeChargeStatus, RefundStatus
from app.payin.core.exceptions import (
    CartPaymentReadError,
    CartPaymentUpdateError,
    PayinErrorCode,
    PaymentMethodReadError,
)
from app.payin.core.payer.payer_client import PayerClient
from app.payin.core.payment_method.processor import PaymentMethodClient
from app.payin.tests.utils import (
    FunctionMock,
    generate_cart_payment,
    generate_legacy_consumer_charge,
    generate_legacy_payment,
    generate_legacy_stripe_charge,
    generate_payment_intent,
    generate_payment_intent_adjustment_history,
    generate_pgp_payment_intent,
    generate_pgp_refund,
    generate_refund,
)


class TestCartPaymentProcessor:
    """
    Test external facing functions exposed by app/payin/core/cart_payment/processor.py.
    """

    @pytest.fixture
    def request_cart_payment(self):
        return generate_cart_payment()

    @pytest.fixture
    def payment_method_client(self):
        return PaymentMethodClient(
            payment_method_repo=MagicMock(), log=MagicMock(), app_ctxt=MagicMock()
        )

    @pytest.fixture
    def payer_client(self):
        return PayerClient(
            payer_repo=MagicMock(), log=MagicMock(), app_ctxt=MagicMock()
        )

    def test_get_legacy_client_description(self, cart_payment_processor):
        # Value < 1000: not modified
        input_value = "test"
        result = cart_payment_processor.get_legacy_client_description(input_value)
        assert result == input_value

        # Value over 1000: modified
        input_value = """
            #order_cart_adjustment# Hi Test Name,

            This email is to confirm that we have edited your DoorDash order.
            The new total cost of your order is $15.00 which includes
            all taxes and fees.

            Please note, you might see a refund for the
            original order amount and a new, separate charge reflecting the final
            adjusted order total of $15.00 in your account.

            You can verify the final order total charge in your account by
            visiting www.DoorDash.com and following these steps:
                1. Click the 3 stacked bars to access the site menu.
                2. Click Orders from the menu list.
                3. Click on the relevant order to review the details, including order total.

            The refund of your original order total and the updated final order total
            charge can take between 5-7 business days to complete, depending on your
            bank’s processing times.

            Thanks again for ordering with DoorDash.
            Please feel free to contact us if there’s anything else we can help with.

            Best,
            Varun
            DoorDash Customer Care
            support.doordash.com"
            """

        result = cart_payment_processor.get_legacy_client_description(input_value)
        assert result == input_value[:1000]

        # Not provided case
        result = cart_payment_processor.get_legacy_client_description(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_payment_with_no_payment_method(
        self,
        request_cart_payment,
        payer_client,
        payment_method_client,
        cart_payment_repo,
    ):
        mocked_method_fetch = FunctionMock()
        mocked_method_fetch.side_effect = PaymentMethodReadError(
            error_code=PayinErrorCode.PAYMENT_METHOD_GET_NOT_FOUND, retryable=False
        )
        payment_method_client.get_raw_payment_method = mocked_method_fetch

        cart_payment_interface = processor.CartPaymentInterface(
            app_context=MagicMock(),
            req_context=MagicMock(),
            payer_client=payer_client,
            payment_method_client=payment_method_client,
            payment_repo=cart_payment_repo,
        )
        legacy_payment_interface = processor.LegacyPaymentInterface(
            app_context=MagicMock(),
            req_context=MagicMock(),
            payment_repo=cart_payment_repo,
        )
        cart_payment_processor = processor.CartPaymentProcessor(
            log=MagicMock(),
            cart_payment_interface=cart_payment_interface,
            legacy_payment_interface=legacy_payment_interface,
        )

        with pytest.raises(PaymentMethodReadError) as payment_error:
            await cart_payment_processor.create_payment(
                request_cart_payment=request_cart_payment,
                idempotency_key=str(uuid.uuid4()),
                payment_country=CountryCode.US,
                currency=Currency.USD,
            )
        assert (
            payment_error.value.error_code
            == PayinErrorCode.PAYMENT_METHOD_GET_NOT_FOUND.value
        )

    @pytest.mark.asyncio
    async def test_create_payment_with_other_owner(
        self,
        cart_payment_repo,
        request_cart_payment,
        payer_client,
        payment_method_client,
    ):
        mocked_method_fetch = FunctionMock()
        mocked_method_fetch.side_effect = PaymentMethodReadError(
            error_code=PayinErrorCode.PAYMENT_METHOD_GET_PAYER_PAYMENT_METHOD_MISMATCH,
            retryable=False,
        )
        payment_method_client.get_raw_payment_method = mocked_method_fetch

        request_cart_payment.payer_id = f"changed-{request_cart_payment.payer_id}"
        cart_payment_interface = processor.CartPaymentInterface(
            app_context=MagicMock(),
            req_context=MagicMock(),
            payment_repo=cart_payment_repo,
            payer_client=payer_client,
            payment_method_client=payment_method_client,
        )
        legacy_payment_interface = processor.LegacyPaymentInterface(
            app_context=MagicMock(),
            req_context=MagicMock(),
            payment_repo=cart_payment_repo,
        )
        cart_payment_processor = processor.CartPaymentProcessor(
            log=MagicMock(),
            cart_payment_interface=cart_payment_interface,
            legacy_payment_interface=legacy_payment_interface,
        )

        with pytest.raises(PaymentMethodReadError) as payment_error:
            await cart_payment_processor.create_payment(
                request_cart_payment=request_cart_payment,
                idempotency_key=str(uuid.uuid4()),
                payment_country=CountryCode.US,
                currency=Currency.USD,
            )
        assert (
            payment_error.value.error_code
            == PayinErrorCode.PAYMENT_METHOD_GET_PAYER_PAYMENT_METHOD_MISMATCH.value
        )

    @pytest.mark.skip("Not yet implemented")
    @pytest.mark.asyncio
    async def test_legacy_payment(self):
        # TODO legacy payment, including other payer_id_type
        pass

    @pytest.mark.asyncio
    async def test_create_payment(self, cart_payment_processor, request_cart_payment):
        result_cart_payment = await cart_payment_processor.create_payment(
            request_cart_payment=request_cart_payment,
            idempotency_key=str(uuid.uuid4()),
            payment_country=CountryCode.US,
            currency=Currency.USD,
        )
        assert result_cart_payment
        assert result_cart_payment.id
        assert result_cart_payment.amount == request_cart_payment.amount
        assert (
            result_cart_payment.client_description
            == request_cart_payment.client_description
        )

    @pytest.mark.asyncio
    async def test_create_payment_with_exception_calling_provider(
        self, cart_payment_processor, request_cart_payment
    ):
        cart_payment_processor._update_state_after_provider_error = FunctionMock()
        cart_payment_processor._get_payer_from_cart_payment = FunctionMock()
        cart_payment_processor.cart_payment_interface.submit_payment_to_provider = FunctionMock(
            side_effect=Exception()
        )

        with pytest.raises(Exception):
            await cart_payment_processor.create_payment(
                request_cart_payment=request_cart_payment,
                idempotency_key=str(uuid.uuid4()),
                payment_country=CountryCode.US,
                currency=Currency.USD,
            )

        assert cart_payment_processor._update_state_after_provider_error.called is True

    @pytest.mark.asyncio
    async def test_create_commando_payment(
        self, cart_payment_processor, request_cart_payment
    ):
        cart_payment_processor.cart_payment_interface.stripe_async_client.commando = (
            True
        )
        result_cart_payment = await cart_payment_processor.create_payment(
            request_cart_payment=request_cart_payment,
            idempotency_key=str(uuid.uuid4()),
            payment_country=CountryCode.US,
            currency=Currency.USD,
        )
        assert result_cart_payment
        assert result_cart_payment.id
        assert result_cart_payment.amount == request_cart_payment.amount
        assert (
            result_cart_payment.client_description
            == request_cart_payment.client_description
        )

    @pytest.mark.asyncio
    async def test_resubmit(self, cart_payment_processor, request_cart_payment):

        intent = generate_payment_intent()
        cart_payment_processor.cart_payment_interface.payment_repo.get_payment_intent_for_idempotency_key = FunctionMock(
            return_value=intent
        )
        cart_payment_processor.cart_payment_interface.payment_repo.find_pgp_payment_intents = FunctionMock(
            return_value=[generate_pgp_payment_intent(payment_intent_id=intent.id)]
        )

        legacy_payment = generate_legacy_payment()
        cart_payment_processor.cart_payment_interface.payment_repo.get_cart_payment_by_id = FunctionMock(
            return_value=(request_cart_payment, legacy_payment)
        )
        cart_payment_processor.legacy_payment_interface.find_existing_payment_charge = FunctionMock(
            return_value=(
                generate_legacy_consumer_charge(),
                generate_legacy_stripe_charge(),
            )
        )

        # Submit when lookup functions mocked above return a result, meaning we have existing cart payment/intent
        result_cart_payment = await cart_payment_processor.create_payment(
            request_cart_payment=request_cart_payment,
            idempotency_key=str(uuid.uuid4()),
            payment_country=CountryCode.US,
            currency=Currency.USD,
        )
        assert result_cart_payment

        cart_payment_processor.cart_payment_interface.payment_repo.get_cart_payment_by_id = FunctionMock(
            return_value=(result_cart_payment, legacy_payment)
        )

        # Second submission attempt
        second_result_cart_payment = await cart_payment_processor.create_payment(
            request_cart_payment=request_cart_payment,
            idempotency_key=str(uuid.uuid4()),
            payment_country=CountryCode.US,
            currency=Currency.USD,
        )
        assert second_result_cart_payment
        assert result_cart_payment == second_result_cart_payment

    @pytest.mark.asyncio
    async def test_update_fake_cart_payment(self, cart_payment_processor):
        cart_payment_processor.cart_payment_interface.payment_repo.get_cart_payment_by_id = FunctionMock(
            return_value=(None, None)
        )

        with pytest.raises(CartPaymentReadError) as payment_error:
            await cart_payment_processor.update_payment(
                idempotency_key=str(uuid.uuid4()),
                cart_payment_id=uuid.uuid4(),
                payer_id="payer_id",
                amount=500,
                client_description=None,
                split_payment=None,
            )
        assert (
            payment_error.value.error_code
            == PayinErrorCode.CART_PAYMENT_NOT_FOUND.value
        )

    @pytest.mark.asyncio
    async def test_update_payment_higher(self, cart_payment_processor):
        cart_payment = generate_cart_payment()
        updated_amount = cart_payment.amount + 100
        result = await cart_payment_processor.update_payment(
            idempotency_key=str(uuid.uuid4()),
            cart_payment_id=cart_payment.id,
            payer_id=cart_payment.payer_id,
            amount=updated_amount,
            client_description=None,
            split_payment=SplitPayment(
                payout_account_id="test_merchant", application_fee_amount=20
            ),
        )
        assert result
        assert result.id == cart_payment.id
        assert result.amount == updated_amount

    @pytest.mark.asyncio
    async def test_update_payment_with_higher_amount(self, cart_payment_processor):
        cart_payment = generate_cart_payment(amount=650)
        idempotency_key = str(uuid.uuid4())
        new_amount = 750
        intents_for_cart_payment = [
            generate_payment_intent(
                cart_payment_id=cart_payment.id,
                status=IntentStatus.REQUIRES_CAPTURE,
                idempotency_key=idempotency_key,
            )
        ]
        cart_payment_processor.cart_payment_interface.get_cart_payment_intents = FunctionMock(
            return_value=intents_for_cart_payment
        )
        cart_payment_processor.cart_payment_interface.payment_repo.update_payment_intent_status = FunctionMock(
            return_value=generate_payment_intent(
                id=intents_for_cart_payment[0].id,
                amount=new_amount,
                status=IntentStatus.REQUIRES_CAPTURE,
            )
        )

        result_intent, result_pgp_intent = await cart_payment_processor._update_payment_with_higher_amount(
            cart_payment=cart_payment,
            legacy_payment=None,
            idempotency_key=str(uuid.uuid4()),
            payer_country=CountryCode.US,
            amount=new_amount,
            description=None,
            split_payment=None,
        )
        assert result_intent.amount == new_amount
        assert result_intent.status == IntentStatus.REQUIRES_CAPTURE

        # Resubmit where intent processing with provider did not finish
        intents_for_cart_payment = [
            generate_payment_intent(
                cart_payment_id=cart_payment.id,
                status=IntentStatus.INIT,
                idempotency_key=idempotency_key,
            )
        ]
        cart_payment_processor.cart_payment_interface.get_cart_payment_intents = FunctionMock(
            return_value=intents_for_cart_payment
        )
        cart_payment_processor.legacy_payment_interface.find_existing_payment_charge = FunctionMock(
            return_value=(
                generate_legacy_consumer_charge(),
                generate_legacy_stripe_charge(),
            )
        )

        result_intent, result_pgp_intent = await cart_payment_processor._update_payment_with_higher_amount(
            cart_payment=cart_payment,
            legacy_payment=None,
            idempotency_key=idempotency_key,
            payer_country=CountryCode.US,
            amount=new_amount,
            description=None,
            split_payment=None,
        )
        assert result_intent.amount == new_amount
        assert result_intent.status == IntentStatus.REQUIRES_CAPTURE

        # Resubmit where intent processing with provider did already finish
        intents_for_cart_payment = [
            generate_payment_intent(
                cart_payment_id=cart_payment.id,
                status=IntentStatus.REQUIRES_CAPTURE,
                idempotency_key=idempotency_key,
            )
        ]
        cart_payment_processor.cart_payment_interface.get_cart_payment_intents = FunctionMock(
            return_value=intents_for_cart_payment
        )

        result_intent, result_pgp_intent = await cart_payment_processor._update_payment_with_higher_amount(
            cart_payment=cart_payment,
            legacy_payment=None,
            idempotency_key=idempotency_key,
            payer_country=CountryCode.US,
            amount=new_amount,
            description=None,
            split_payment=None,
        )
        assert result_intent == intents_for_cart_payment[0]

    @pytest.mark.asyncio
    async def test_update_payment_amount_lower(self, cart_payment_processor):
        cart_payment = generate_cart_payment()
        cart_payment_processor.cart_payment_interface.get_cart_payment_intents = FunctionMock(
            return_value=[
                generate_payment_intent(
                    cart_payment_id=cart_payment.id,
                    status=IntentStatus.REQUIRES_CAPTURE,
                )
            ]
        )

        updated_amount = cart_payment.amount - 100
        result = await cart_payment_processor.update_payment(
            idempotency_key=str(uuid.uuid4()),
            cart_payment_id=cart_payment.id,
            payer_id=cart_payment.payer_id,
            amount=updated_amount,
            client_description=None,
            split_payment=None,
        )
        assert result
        assert result.id == cart_payment.id
        assert result.amount == updated_amount

    @pytest.mark.asyncio
    async def test_update_payment_with_lower_amount_for_uncaptured(
        self, cart_payment_processor
    ):
        cart_payment = generate_cart_payment(amount=880)
        idempotency_key = str(uuid.uuid4())
        new_amount = 800

        intents_for_cart_payment = [
            generate_payment_intent(
                cart_payment_id=cart_payment.id, status=IntentStatus.REQUIRES_CAPTURE
            )
        ]
        cart_payment_processor.cart_payment_interface.get_cart_payment_intents = FunctionMock(
            return_value=intents_for_cart_payment
        )
        cart_payment_processor.cart_payment_interface.payment_repo.update_payment_intent_amount = FunctionMock(
            return_value=generate_payment_intent(
                status=IntentStatus.REQUIRES_CAPTURE, amount=new_amount
            )
        )
        cart_payment_processor.cart_payment_interface.payment_repo.find_pgp_payment_intents = FunctionMock(
            return_value=[
                generate_pgp_payment_intent(
                    status=IntentStatus.REQUIRES_CAPTURE, amount=new_amount
                )
            ]
        )

        result_intent, result_pgp_intent = await cart_payment_processor._update_payment_with_lower_amount(
            cart_payment=cart_payment,
            new_amount=new_amount,
            idempotency_key=idempotency_key,
        )

        assert result_intent.status == IntentStatus.REQUIRES_CAPTURE
        assert result_intent.amount == 800
        assert result_pgp_intent.status == IntentStatus.REQUIRES_CAPTURE
        assert result_pgp_intent.amount == 800

        # Resubmit
        cart_payment_processor.cart_payment_interface.get_payment_intent_adjustment = FunctionMock(
            return_value=generate_payment_intent_adjustment_history()
        )
        result_intent, result_pgp_intent = await cart_payment_processor._update_payment_with_lower_amount(
            cart_payment=cart_payment,
            new_amount=new_amount,
            idempotency_key=idempotency_key,
        )
        assert result_intent == intents_for_cart_payment[0]

    @pytest.mark.asyncio
    async def test_update_payment_with_lower_amount_for_refund(
        self, cart_payment_processor
    ):
        cart_payment = generate_cart_payment(amount=780)
        idempotency_key = str(uuid.uuid4())
        new_amount = 700

        intents_for_cart_payment = [
            generate_payment_intent(
                cart_payment_id=cart_payment.id, status=IntentStatus.SUCCEEDED
            )
        ]
        cart_payment_processor.cart_payment_interface.get_cart_payment_intents = FunctionMock(
            return_value=intents_for_cart_payment
        )
        cart_payment_processor.cart_payment_interface.payment_repo.update_payment_intent_amount = FunctionMock(
            return_value=generate_payment_intent(
                status=IntentStatus.SUCCEEDED, amount=new_amount
            )
        )
        cart_payment_processor.cart_payment_interface.payment_repo.update_pgp_payment_intent_amount = FunctionMock(
            return_value=generate_pgp_payment_intent(
                status=IntentStatus.SUCCEEDED, amount=new_amount
            )
        )

        result_intent, result_pgp_intent = await cart_payment_processor._update_payment_with_lower_amount(
            cart_payment=cart_payment,
            new_amount=new_amount,
            idempotency_key=idempotency_key,
        )

        assert result_intent.status == IntentStatus.SUCCEEDED
        assert result_intent.amount == 700
        assert result_pgp_intent.status == IntentStatus.SUCCEEDED
        assert result_pgp_intent.amount == 700

        # Simulate resubmit after previous request that did not complete successfully:
        # Refund created, but not processed completely.
        cart_payment_processor.cart_payment_interface.find_existing_refund = FunctionMock(
            return_value=(
                generate_refund(status=RefundStatus.PROCESSING),
                generate_pgp_refund(status=RefundStatus.PROCESSING),
            )
        )
        resubmit_intent, resubmit_pgp_intent = await cart_payment_processor._update_payment_with_lower_amount(
            cart_payment=cart_payment,
            new_amount=new_amount,
            idempotency_key=idempotency_key,
        )
        assert resubmit_intent == result_intent
        assert resubmit_pgp_intent == result_pgp_intent

        # Simulate resubmit of previous request that completed in provider but not on our end
        cart_payment_processor.cart_payment_interface.find_existing_refund = FunctionMock(
            return_value=(
                generate_refund(status=RefundStatus.SUCCEEDED),
                generate_pgp_refund(status=RefundStatus.SUCCEEDED),
            )
        )
        resubmit_intent, resubmit_pgp_intent = await cart_payment_processor._update_payment_with_lower_amount(
            cart_payment=cart_payment,
            new_amount=new_amount,
            idempotency_key=idempotency_key,
        )
        assert resubmit_intent == intents_for_cart_payment[0]

    @pytest.mark.asyncio
    async def test_cancel_payment_intent_for_uncaptured(self, cart_payment_processor):
        cart_payment = generate_cart_payment()
        payment_intent = generate_payment_intent(
            cart_payment_id=cart_payment.id, status=IntentStatus.REQUIRES_CAPTURE
        )
        result_intent, result_pgp_intent = await cart_payment_processor._cancel_payment_intent(
            cart_payment, payment_intent
        )
        assert result_intent.status == IntentStatus.CANCELLED
        assert result_pgp_intent.status == IntentStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_payment_intent_for_captured(self, cart_payment_processor):
        cart_payment = generate_cart_payment()
        payment_intent = generate_payment_intent(
            cart_payment_id=cart_payment.id, status=IntentStatus.SUCCEEDED
        )
        result_intent, result_pgp_intent = await cart_payment_processor._cancel_payment_intent(
            cart_payment, payment_intent
        )
        # TODO verify expected values
        assert result_intent.amount == 0
        assert result_pgp_intent.amount == 0

    @pytest.mark.asyncio
    async def test_update_state_after_provider_error(self, cart_payment_processor):
        payment_intent = generate_payment_intent()
        pgp_payment_intent = generate_pgp_payment_intent()
        legacy_stripe_charge = generate_legacy_stripe_charge()

        result_intent, result_pgp_intent, result_stripe_charge = await cart_payment_processor._update_state_after_provider_error(
            payment_intent=payment_intent,
            pgp_payment_intent=pgp_payment_intent,
            legacy_stripe_charge=legacy_stripe_charge,
        )

        assert result_intent.status == IntentStatus.FAILED
        assert result_pgp_intent.status == IntentStatus.FAILED
        assert result_stripe_charge.status == LegacyStripeChargeStatus.FAILED

    @pytest.mark.asyncio
    async def test_update_state_after_refund_with_provider(
        self, cart_payment_processor
    ):
        cart_payment = generate_cart_payment()
        payment_intent = generate_payment_intent(
            cart_payment_id=cart_payment.id, status=IntentStatus.SUCCEEDED
        )
        pgp_payment_intent = generate_pgp_payment_intent(
            payment_intent_id=payment_intent.id, status=IntentStatus.SUCCEEDED
        )

        refund = generate_refund()
        pgp_refund = generate_pgp_refund()

        provider_refund = (
            await cart_payment_processor.cart_payment_interface.app_context.stripe.refund_charge()
        )

        result_payment_intent, result_pgp_payment_intent = await cart_payment_processor._update_state_after_refund_with_provider(
            payment_intent=payment_intent,
            pgp_payment_intent=pgp_payment_intent,
            provider_refund=provider_refund,
            refund_amount=payment_intent.amount,
            refund=refund,
            pgp_refund=pgp_refund,
        )

        # TODO verify expected values
        assert result_payment_intent.amount == 0
        assert result_pgp_payment_intent.amount == 0

    @pytest.mark.asyncio
    async def test_update_state_after_cancel_with_provider(
        self, cart_payment_processor
    ):
        cart_payment = generate_cart_payment()
        payment_intent = generate_payment_intent(
            cart_payment_id=cart_payment.id, status=IntentStatus.REQUIRES_CAPTURE
        )
        pgp_payment_intent = generate_pgp_payment_intent(
            payment_intent_id=payment_intent.id, status=IntentStatus.REQUIRES_CAPTURE
        )

        provider_payment_intent = (
            await cart_payment_processor.cart_payment_interface.app_context.stripe.create_payment_intent()
        )

        result_payment_intent, result_pgp_payment_intent, result_legacy_stripe_charge = await cart_payment_processor._update_state_after_cancel_with_provider(
            payment_intent=payment_intent,
            pgp_payment_intent=pgp_payment_intent,
            provider_payment_intent=provider_payment_intent,
        )

        assert result_payment_intent.status == IntentStatus.CANCELLED
        assert result_pgp_payment_intent.status == IntentStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_update_state_after_submit_to_provider(self, cart_payment_processor):
        cart_payment = generate_cart_payment()
        payment_intent = generate_payment_intent(
            cart_payment_id=cart_payment.id, status=IntentStatus.REQUIRES_CAPTURE
        )
        pgp_payment_intent = generate_pgp_payment_intent(
            payment_intent_id=payment_intent.id, status=IntentStatus.REQUIRES_CAPTURE
        )

        provider_payment_intent = (
            await cart_payment_processor.cart_payment_interface.app_context.stripe.create_payment_intent()
        )

        # update legacy values in db
        result_stripe_charge = await cart_payment_processor.legacy_payment_interface.update_state_after_provider_submission(
            idempotency_key=str(uuid.uuid4()),
            provider_payment_intent=provider_payment_intent,
            legacy_stripe_charge=generate_legacy_stripe_charge(),
        )

        # update payment_intent and pgp_payment_intent pair in db
        result_payment_intent, result_pgp_payment_intent = await cart_payment_processor.cart_payment_interface.update_state_after_provider_submission(
            payment_intent=payment_intent,
            pgp_payment_intent=pgp_payment_intent,
            provider_payment_intent=provider_payment_intent,
        )

        assert result_payment_intent.status == IntentStatus.REQUIRES_CAPTURE
        assert result_pgp_payment_intent.status == IntentStatus.REQUIRES_CAPTURE
        assert result_stripe_charge.status == LegacyStripeChargeStatus.SUCCEEDED

    @pytest.mark.asyncio
    async def test_cancel_payment(self, cart_payment_processor, request_cart_payment):
        result = await cart_payment_processor.cancel_payment(request_cart_payment.id)
        assert result
        assert type(result) == CartPayment

    @pytest.mark.asyncio
    async def test_cancel_payment_fake_cart_payment(self, cart_payment_processor):
        cart_payment_processor.cart_payment_interface.payment_repo.get_cart_payment_by_id = FunctionMock(
            return_value=(None, None)
        )

        with pytest.raises(CartPaymentReadError) as payment_error:
            await cart_payment_processor.cancel_payment(cart_payment_id=uuid.uuid4())
        assert (
            payment_error.value.error_code
            == PayinErrorCode.CART_PAYMENT_NOT_FOUND.value
        )

    @pytest.mark.asyncio
    async def test_update_payment_for_legacy_charge(self, cart_payment_processor):
        legacy_charge = generate_legacy_consumer_charge()
        legacy_payment = generate_legacy_payment()
        cart_payment = generate_cart_payment(amount=700)
        cart_payment_processor.cart_payment_interface.get_cart_payment = FunctionMock(
            return_value=(cart_payment, legacy_payment)
        )
        client_description = f"updated description for {legacy_charge.id}"
        result = await cart_payment_processor.update_payment_for_legacy_charge(
            idempotency_key=str(uuid.uuid4()),
            dd_charge_id=legacy_charge.id,
            amount=150,
            client_description=client_description,
            dd_additional_payment_info=legacy_payment.dd_additional_payment_info,
            split_payment=None,
        )
        assert result
        assert result.amount == cart_payment.amount + 150
        assert result.client_description == client_description

    @pytest.mark.asyncio
    async def test_update_payment_for_legacy_charge_fake_cart_payment(
        self, cart_payment_processor
    ):
        legacy_charge = generate_legacy_consumer_charge()
        cart_payment_processor.legacy_payment_interface.payment_repo.get_payment_intent_for_legacy_consumer_charge_id = FunctionMock(
            return_value=None
        )
        with pytest.raises(CartPaymentReadError) as payment_error:
            await cart_payment_processor.update_payment_for_legacy_charge(
                idempotency_key=str(uuid.uuid4()),
                dd_charge_id=legacy_charge.id,
                amount=1500,
                client_description="description",
                dd_additional_payment_info=None,
                split_payment=None,
            )
        assert (
            payment_error.value.error_code
            == PayinErrorCode.CART_PAYMENT_NOT_FOUND.value
        )

    @pytest.mark.asyncio
    async def test_update_payment_for_legacy_charge_invalid_amount(
        self, cart_payment_processor
    ):
        legacy_charge = generate_legacy_consumer_charge()
        legacy_charge = generate_legacy_consumer_charge()
        legacy_payment = generate_legacy_payment()
        cart_payment = generate_cart_payment(amount=700)
        cart_payment_processor.cart_payment_interface.get_cart_payment = FunctionMock(
            return_value=(cart_payment, legacy_payment)
        )

        with pytest.raises(CartPaymentUpdateError) as payment_error:
            await cart_payment_processor.update_payment_for_legacy_charge(
                idempotency_key=str(uuid.uuid4()),
                dd_charge_id=legacy_charge.id,
                amount=-1500,
                client_description="description",
                dd_additional_payment_info=None,
                split_payment=None,
            )
        assert (
            payment_error.value.error_code
            == PayinErrorCode.CART_PAYMENT_AMOUNT_INVALID.value
        )

    @pytest.mark.asyncio
    async def test_cancel_payment_for_legacy_charge(self, cart_payment_processor):
        legacy_charge = generate_legacy_consumer_charge()
        result = await cart_payment_processor.cancel_payment_for_legacy_charge(
            dd_charge_id=legacy_charge.id
        )
        assert result
        assert type(result) == CartPayment

    @pytest.mark.asyncio
    async def test_cancel_payment_for_legacy_charge_fake_cart_payment(
        self, cart_payment_processor
    ):
        legacy_charge = generate_legacy_consumer_charge()
        cart_payment_processor.legacy_payment_interface.payment_repo.get_payment_intent_for_legacy_consumer_charge_id = FunctionMock(
            return_value=None
        )

        with pytest.raises(CartPaymentReadError) as payment_error:
            await cart_payment_processor.cancel_payment_for_legacy_charge(
                dd_charge_id=legacy_charge.id
            )
        assert (
            payment_error.value.error_code
            == PayinErrorCode.CART_PAYMENT_NOT_FOUND.value
        )
