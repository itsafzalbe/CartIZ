# 3. COMMUNICATIONS APP (44 serializers)
# Notifications:
#
# NotificationSerializer - Views single notification details
# NotificationListSerializer - Lists all user notifications with pagination
# NotificationCreateSerializer - Creates new notification (system use)
# NotificationUpdateSerializer - Updates notification status
# NotificationDeleteSerializer - Deletes single notification
# NotificationMarkReadSerializer - Marks notification as read
# NotificationMarkAllReadSerializer - Marks all notifications as read
# NotificationUnreadCountSerializer - Returns count of unread notifications
# NotificationBulkDeleteSerializer - Deletes multiple notifications
#
# Notification Preferences:
#
# NotificationPreferenceSerializer - Views user notification preferences
# NotificationPreferenceUpdateSerializer - Updates notification settings
# EmailNotificationPreferenceSerializer - Manages email notification preferences
# PushNotificationPreferenceSerializer - Manages push notification preferences
#
# Messages:
#
# MessageSerializer - Views single message details
# MessageCreateSerializer - Sends new message to user/seller
# MessageUpdateSerializer - Edits existing message
# MessageDeleteSerializer - Deletes message
# MessageListSerializer - Lists all messages with pagination
# MessageDetailSerializer - Shows message with full sender/receiver info
# MessageMarkReadSerializer - Marks message as read
# MessageBulkDeleteSerializer - Deletes multiple messages
# MessageUnreadCountSerializer - Returns count of unread messages
#
# Conversations:
#
# ConversationSerializer - Views conversation thread
# ConversationListSerializer - Lists all user conversations
# ConversationDetailSerializer - Shows full conversation with all messages
# ConversationCreateSerializer - Starts new conversation
# ConversationDeleteSerializer - Deletes entire conversation
# ConversationUnreadCountSerializer - Returns unread messages count per conversation
# ConversationSearchSerializer - Searches through conversations
#
# Support Tickets:
#
# SupportTicketSerializer - Views support ticket details
# SupportTicketCreateSerializer - Creates new support ticket
# SupportTicketUpdateSerializer - Updates ticket status or details
# SupportTicketDeleteSerializer - Deletes support ticket
# SupportTicketListSerializer - Lists all support tickets with filters
# SupportTicketDetailSerializer - Shows ticket with all replies
# SupportTicketCloseSerializer - Closes resolved ticket
# SupportTicketReopenSerializer - Reopens closed ticket
# SupportTicketAssignSerializer - Assigns ticket to support agent
# SupportTicketStatsSerializer - Returns ticket statistics (open, closed, response time)
#
# Ticket Replies:
#
# TicketReplySerializer - Views single ticket reply
# TicketReplyCreateSerializer - Adds reply to support ticket
# TicketReplyUpdateSerializer - Edits ticket reply
# TicketReplyDeleteSerializer - Deletes ticket reply
# TicketReplyListSerializer - Lists all replies in a ticket