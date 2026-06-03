from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from apps.accounts.models import User




class Banner(models.Model):
    HERO        = 'hero'
    PROMOTIONAL = 'promotional'
    SLIDER      = 'slider'
    CATEGORY    = 'category'

    BANNER_TYPE = (
        (HERO,        'Hero'),
        (PROMOTIONAL, 'Promotional'),
        (SLIDER,      'Slider'),
        (CATEGORY,    'Category'),
    )

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='banners/')
    mobile_image = models.ImageField(upload_to='banners/mobile/', null=True, blank=True)
    link_url = models.URLField(blank=True, help_text="CTA destination URL")
    link_text = models.CharField(max_length=100, blank=True, help_text="CTA button text")
    banner_type = models.CharField(max_length=20, choices=BANNER_TYPE, default=SLIDER)
    position = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    click_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'banners'
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'
        ordering = ['position', '-created_at']
        indexes = [
            models.Index(fields=['banner_type', 'is_active']),
            models.Index(fields=['position']),
        ]
    
    def __str__(self):
        return f"[{self.get_banner_type_display()}] {self.title}"
    
    @property
    def is_live(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True


    @property
    def image_url(self):
        return self.image.url if self.image else None
    
    @property
    def mobile_image_url(self):
        return self.mobile_image.url if self.mobile_image else None






class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=50, default='homepage', help_text='Where they subscribed from')
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateField(null=True, blank=True)

    class Meta:
        db_table            = 'newsletter_subscribers'
        verbose_name        = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    PENDING = 'pending'
    REVIEWED = 'reviewed'
    RESOLVED = 'resolved'

    STATUS = (
        (PENDING, 'Pending'),
        (REVIEWED, 'Reviewed'),
        (RESOLVED, 'Resolved'),
    )
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default=PENDING)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contact_message'
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.subject}"


class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.CharField(max_length=255)
    result_count = models.PositiveIntegerField(default=0)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'search_history'
        verbose_name = 'Search History'
        verbose_name_plural = 'Search History'
        ordering = ['-searched_at']
        indexes = [
            models.Index(fields=['user', 'searched_at']),
            models.Index(fields=['query']),
        ]
    
    def __str__(self):
        return f"{self.user} - '{self.query}'"



class PopularSearch(models.Model):
    query = models.CharField(max_length=255, unique=True)
    count = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'popular_searches'
        verbose_name = 'Popular Search'
        verbose_name_plural = 'Popular Searches'
        ordering = ['-count']
        indexes = [
            models.Index(fields=['-count']),
        ]
    
    def __str__(self):
        return f"'{self.query}' ({self.count})"


class PageView(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='page_views')
    path = models.CharField(max_length=500, help_text="URL path viewed")
    refferer = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'page_views'
        verbose_name = 'Page View'
        verbose_name_plural = 'Page Views'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['path', 'viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
        ]
    
    def __str__(self):
        return f"{self.path} @ {self.viewed_at:%Y-%m-%d %H:%M}"


class AnalyticsEvent(models.Model):
    CLICK       = 'click'
    VIEW        = 'view'
    ADD_TO_CART = 'add_to_cart'
    PURCHASE    = 'purchase'
    SEARCH      = 'search'
    CUSTOM      = 'custom'
    
    EVENT_TYPES = (
        (CLICK,       'Click'),
        (VIEW,        'View'),
        (ADD_TO_CART, 'Add to Cart'),
        (PURCHASE,    'Purchase'),
        (SEARCH,      'Search'),
        (CUSTOM,      'Custom'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='analytics_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    category = models.CharField(max_length=100, blank=True, help_text='e.g. product, banner, category')
    label = models.CharField(max_length=255, blank=True, help_text='Identifier for the element')
    value = models.CharField(max_length=255, blank=True, help_text='Optional value/metadata')
    path = models.CharField(max_length=500, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True, help_text="Extra structured data")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_events'
        verbose_name = 'Analytics Event'
        verbose_name_plural = 'Analytics Events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['category', 'label']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.category}/{self.label}"
