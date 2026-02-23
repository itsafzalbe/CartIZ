from django.db import models

# Create your models here.



# NOTIFICATION
# MESSAGE
# SUPPORT_TICKET
# SUPPORT_TICKET_REPLY


class Notification(models.Model):
    user_id = 
    type = 
    title =
    message = 
    link = 
    is_read= 
    created_at =
    read_at = 

class Message(models.Model):
    sender_id
    receiver_id
    product_id
    order_id
    subject
    message
    is_read
    created_at
    read_at


class SupportTicket(models.Model):
    ticket_number
    user_id
    order_id
    category
    priority
    status
    subject
    description
    assigned_to
    created_at
    updated_at
    resolved_at


class SupportTicketReply(models.Model):
    ticket_id
    user_id
    message
    is_staff_reply
    created_at
    
