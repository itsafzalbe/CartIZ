from django.db import models
from apps.accounts.models import *
from django.utils.timezone import now
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db.models import Q
from orders.models import Order
from django.core.exceptions import ValidationError

# USER_CARD
# CARD_TRANSACTION
# PAYMENT
# REFUND

def current_year():
    return now().year


class UserCard(models.Model):
    CARD_TYPES = (
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_cards")
    card_number = models.CharField(max_length=19, validators=[RegexValidator(r'^\d{13,19}$', 'Enter a valid card number')], help_text="Card number")
    card_holder_name = models.CharField(max_length=200, validators=[RegexValidator(r"^[A-Za-z]+(?:'[A-Za-z]+)?(?: [A-Za-z]+(?:'[A-Za-z]+)?)*$", "Enter valid name")], help_text="Card Holder Name")
    expiry_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], help_text="Expiration month")
    expiry_year = models.IntegerField(validators=[MinValueValidator(current_year)], help_text="Expiration year")
    cvv = models.CharField(max_length=4, validators=[RegexValidator(r'^\d{3,4}$', 'Enter Valid CVV')], help_text="Card CVV code")
    card_type = models.CharField(max_length=20, choices=CARD_TYPES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, help_text="Card Balance")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_cards"
        verbose_name = "User Card"
        verbose_name_plural = "User Cards"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['card_number']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=Q(is_default=True),
                name='unique_default_card_per_user'
            )
        ]

    def __str__(self):
        last4 = self.card_number[-4:]
        if self.card_type == 'amex':
            return f"{self.card_type.title()} **** ****** *{last4}"
        return f"{self.card_type.title()} **** **** **** {last4}"





class CardTransaction(models.Model):
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    PAYMENT = 'payment'
    TRANSFER = 'transfer'
    REFUND = 'refund'

    TRANSACTION_TYPES = (
        (DEPOSIT, 'Deposit'),
        (WITHDRAWAL, 'Withdrawal'),
        (PAYMENT, 'Payment'),
        (TRANSFER, 'Transfer'),
        (REFUND, 'Refund'),
    )
    card = models.ForeignKey(UserCard, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(validators=[MinValueValidator(0.01)], max_digits=12, decimal_places=2)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    reference_id = models.CharField(max_length=200, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "card_transactions"
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['card']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} • {self.amount} • {self.card}"
    
    

class Payment(models.Model):

    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    REFUNDED = 'refunded'

    PAYMENT_STATUS = (
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (REFUNDED, 'Refunded'),
    )

    CARD = 'card'
    PAYMENT_METHOD = (
        (CARD, 'Card'),
    )
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    card = models.ForeignKey(UserCard, on_delete=models.PROTECT, related_name="payments")
    transaction_id = models.CharField(max_length=100, unique=True, help_text="Internal transaction ID")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Payment amount")
    currency = models.CharField(max_length=3, default="USD", help_text="Currency code")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default=PENDING, help_text="Payment status")
    payment_method = models.CharField(choices=PAYMENT_METHOD, default=CARD, max_length=50, help_text="Payment method")
    failure_reason = models.TextField(null=True, blank=True, help_text="Reason for failure")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Payment attempt time")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="Success timestamp")

    class Meta:
        db_table = "payments"
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['order'],
                condition=Q(status='completed'),
                name="one_completed_payment_per_order"
            )
        ]
    
    def clean(self):
        if self.status == self.FAILED and not self.failure_reason:
            raise ValidationError("Failure reason required for failed payments")
        
        if self.status == self.COMPLETED and self.failure_reason:
            raise ValidationError("Completed payment cannot have failure reason.")

    def save(self, *args, **kwargs):
        if self.currency:
            self.currency = self.currency.upper()
        
        if self.status == self.COMPLETED and not self.completed_at:
            self.completed_at = now()
        
        self.full_clean()
        super().save(*args, **kwargs)


class Refund(models.Model):
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'

    REFUND_STATUS = (
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="refunds")
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="refunds")
    card = models.ForeignKey(UserCard, on_delete=models.CASCADE, related_name="refunds")
    refund_number = models.CharField(max_length=50, unique=True, help_text="Refund reference number")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Refund amound")
    reason = models.TextField(null=True, blank=True, help_text="Reason for refund")
    status = models.CharField(max_length=10, choices=REFUND_STATUS, help_text="Refund status")
    processed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refunds")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField()
