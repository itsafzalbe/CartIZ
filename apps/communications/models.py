from django.db import models
from accounts.models import User
from products.models import Product
from orders.models import Order
import uuid
# Create your models here.



# NOTIFICATION
# MESSAGE
# SUPPORT_TICKET
# SUPPORT_TICKET_REPLY


class Notification(models.Model):

    ORDER = 'order'
    PAYMENT = 'payment'
    MESSAGE = 'message'
    REVIEW = 'review'
    PROMOTION = 'promotion'
    NOTIFICATION_STATUS = (
        (ORDER, 'Order'),
        (PAYMENT, 'Payment'),
        (MESSAGE, 'Message'),
        (REVIEW, 'Review'),
        (PROMOTION, 'Promotion'),

    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=50, choices=NOTIFICATION_STATUS)
    title = models.CharField(max_length=255, help_text="Notification title")
    message = models.TextField(help_text="Notification content")
    link = models.URLField(null=True, blank=True, help_text="Related link/URL")
    is_read= models.BooleanField(default=False, help_text="Read status")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Creation timestamp")
    read_at = models.DateTimeField(null=True, blank=True, help_text="When marked as read")

    class Meta:
        db_table = "notifications"
        verbose_name = "Notifications"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["-created_at"])
        ]
    
    def __str__(self):
        status = "✓" if self.is_read else "✗"
        return f"[{status}] {self.user} - {self.get_type_display()} - {self.title} ({self.created_at:%Y-%m-%d})"
        

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name="messages")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, related_name="messages")
    subject = models.CharField(max_length=255, null=True, blank=True, help_text="Message subject")
    message = models.TextField(help_text="Message content")
    is_read = models.BooleanField(default=False, help_text="Read status")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Send timestamp")
    read_at = models.DateTimeField(null=True, blank=True, help_text="Read timestamp")

    class Meta:
        db_table = "messages"
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sender"]),
            models.Index(fields=["receiver"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.created_at:%Y-%m-%d})"


class SupportTicket(models.Model):
    ORDER_ISSUE = 'order_issue'
    PAYMENT = 'payment'
    PRODUCT = 'product'
    ACCOUNT = 'account'
    OTHER = 'other'
    CATEGORY = (
        (ORDER_ISSUE, "Order Issue"),
        (PAYMENT, "Payment"),
        (PRODUCT, "Product"),
        (ACCOUNT, "Account"),
        (OTHER, "Other")
    )

    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'

    PRIORITY = (
        (LOW, "Low"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
        (URGENT, "Urgent"),
    )

    OPEN = 'open'
    IN_PROGRESS ='in_progress'
    RESOLVED = 'resolved'
    CLOSED = 'closed'

    STATUS = (
        (OPEN, "Open"),
        (IN_PROGRESS, "In Progress"),
        (RESOLVED, "Resolved"),
        (CLOSED, "Closed")
    )

    ticket_number = models.CharField(max_length=50, unique=True, help_text="Ticket reference")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="support_tickets")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets")
    category = models.CharField(max_length=50, choices=CATEGORY)
    priority = models.CharField(max_length=20, choices=PRIORITY, default=MEDIUM)
    status = models.CharField(max_length=20, choices=STATUS, default=OPEN)
    subject = models.CharField(max_length=255, help_text="Ticket subject")
    description = models.TextField(null=True, blank=True, help_text="Issue description")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Ticket creation time")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last update time")
    resolved_at = models.DateTimeField(null=True, blank=True, help_text="Resolution time")

    class Meta:
        db_table = "support_tickets"
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "status"])
        ]
    
    def __str__(self):
        return f"#{self.ticket_number} | {self.get_status_display()} | {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f"TCK-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)



class SupportTicketReply(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="replies")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ticket_replies")
    message = models.TextField(help_text="Reply content")
    is_staff_reply = models.BooleanField(default=False, help_text="Staff vs customer")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "support_ticket_replies"
        verbose_name = "Support Ticket Reply"
        verbose_name_plural = "Support Ticket Replies"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ticket"])
        ]
    
    def __str__(self):
        return f"Reply by {self.user} - Ticket #{self.ticket.ticket_number}"

