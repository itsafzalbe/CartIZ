from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import serializers

from apps.products.models import Category, Product
from apps.stores.models import Market
from apps.promotions.models import Coupon, Promotion, FlashSale
from .models import (
    AnalyticsEvent, Banner, ContactMessage, 
    NewsletterSubscriber, PageView, PopularSearch, SearchHistory
)

# internal mini-serializers (shape reused across homepage sections)

class _ProductCardMini(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    in_stocka = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'price', 'compare_at_price',
                  'discount_percentage', 'rating_average', 'in_stock', 'primary_image']
        read_only_fields = fields
    
    def get_primary_image(self, obj):
        img = obj.product_images.filter(is_primary=True).first() or obj.product_images.first()
        return img.image.url if img else None

class _MarketMini(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = ['id', 'market_name', 'slug', 'logo_url', 'is_verified', 'rating_average']
        read_only_fields = fields
    
    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None

class _CategoryMini(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon']
        read_only_fields = fields


# HOMEPAGE / DASHBOARD
class BannerSerializer(serializers.ModelSerializer):
    """Single banner - full detail including mobile variant."""
    image_url = serializers.ReadOnlyField()
    mobile_image_url = serializers.ReadOnlyField()
    is_live = serializers.ReadOnlyField()

    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'subtitle', 'description',
            'image_url', 'mobile_image_url',
            'link_url', 'link_text',
            'banner_type', 'position',
            'is_live', 'starts_at', 'ends_at',
        ]
        read_only_fields = fields

class BannerListSerializer(serializers.ModelSerializer):
    """Lightweigth banner row - used for slider / carousel rendering."""
    image_url = serializers.ReadOnlyField()
    mobile_image_url = serializers.ReadOnlyField()

    class Meta:
        model = Banner
        fields = ['id', 'title', 'subtitle', 'image_url', 'mobile_image_url',
                  'link_url', 'link_text', 'position']
        read_only_fields = fields

class PromotionalBannerSerializer(serializers.ModelSerializer):
    """Promotional banner strip - shown below hero."""
    image_url = serializers.ReadOnlyField()

    class Meta:
        model = Banner
        fields = ['id', 'title', 'subtitle', 'image_url', 'link_url', 'link_text']
        read_only_fields = fields

class HeroSectionSerializer(serializers.Serializer):
    """
    Hero section - primary slider banners + headline stats
    Assembled from Banner model.
    """

    def to_representation(self, instance):
        banners = Banner.objects.filter(
            banner_type=Banner.HERO, is_active=True
        ).order_by('position')[:5]

        live_banners = [b for b in banners if b.is_live]

        return {
            'banners': BannerListSerializer(live_banners, many=True).data,
            'stats': {
                'total_products': Product.objects.filter(is_active=True).count(),
                'total_markets':  Market.objects.filter(is_active=True, is_verified=True).count(),
            },
        }


class FeaturedSectionSerializer(serializers.Serializer):
    """
    Featured products section - personalized if user is authenticated
    platform-wide best sellers otherwise
    """

    def to_representation(self, user):
        if user and user.is_authenticated:
            from apps.products.models import WishlistItem
            cat_ids = WishlistItem.objects.filter(wishlist__user=user).values_list('product__category_id', flat=True).distinct()
            qs = Product.objects.filter(is_active=True, is_featured=True, category_id__in=cat_ids).order_by('-rating_average')[:12]
            if qs.count() < 4:
                qs = Product.objects.filter(is_active=True, is_featured=True).order_by('-sold_count')[:12]
        else:
            qs = Product.objects.filter(is_active=True, is_featured=True).order_by('-sold_count')[:12]
        
        return {
            'title': 'Featured for You' if (user and user.is_authenticated) else 'Featured Products',
            'products': _ProductCardMini(qs, many=True).data,
        }

class TrendingSectionSerializer(serializers.Serializer):
    """Trending section - products + markets trending this week."""

    def to_representation(self, instance):
        since = timezone.now() - timezone.timedelta(days=7)
        prods = Product.objects.filter(is_active=True).order_by('-view_count')[:8]
        markets = Market.objects.filter(is_active=True, is_verified=True).order_by('-total_sales')[:6]

        return {
            'trending_products':    _ProductCardMini(prods, many=True).data,
            'trending_markets':     _MarketMini(markets, many=True).data,
        }

class DealsOfTheDaySerializer(serializers.Serializer):
    """Deals of the day - live flash sales + highest-discount products."""

    def to_representation(self, instance):
        now = timezone.now()

        #active Flash Sales
        flash_sales = FlashSale.objects.filter(is_active=True, starts_at__lte=now, ends_at__gte=now).order_by('-discount_percent')[:3]

        flash_data = []
        for sale in flash_sales:
            products = sale.products.filter(is_active=True)[:6]
            seconds = max(0, int((sale.ends_at - now).total_seconds()))
            flash_data.append({
                'id':               sale.id,
                'title':            sale.title,
                'discount_percent': str(sale.discount_percent),
                'ends_at':          sale.ends_at,
                'seconds_remaining': seconds,
                'products':         _ProductCardMini(products, many=True).data
            })
        
        deals = Promotion.objects.filter(is_active=True, starts_at__lte=now, ends_at__gte=now, discount_percent__isnull=False,).order_by('-discount_percent')[:4]

        return {
            'flash_sales': flash_data,
            'deals':    [
                {
                    'id':               d.id,
                    'title':            d.title,
                    'discount_percent': str(d.discount_percent),
                    'ends_at':          d.ends_at,
                    'image_url':        d.image.url if d.image else None,
                }
                for d in deals
            ],
        }
    

class NewsletterSubscribeSerializer(serializers.Serializer):
    """
    Handles newsletter subscription.
    POST /home/newsletter/subscribe/
    """
    email = serializers.EmailField()
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    source = serializers.CharField(max_length=50, required=False, default='homepage')

    def validate_email(self, value):
        value = value.lower().strip()
        sub = NewsletterSubscriber.objects.filter(email=value).first()
        if sub and sub.is_active:
            raise serializers.ValidationError("This email is already subscribed.")
        self._existing = sub
        return value
    
    def save(self):
        data = self.validated_data
        if self._existing:
            # Re-subscribe
            self._existing.is_active        = True
            self._existing.unsubscribed_at  = None
            self._existing.name             = data.get('name', self._existing.name)
            self._existing.save(update_fields=['is_active', 'unsubscribed_at', 'name'])
            return self._existing
        return NewsletterSubscriber.objects.create(
            email=data['email'],
            name=data.get('name', ''),
            source=data.get('source', 'homepage')
        )

class ContactFormSerializer(serializers.Serializer):
    """
    Processes contact from submission.
    POST /home/contact/
    """
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=255)
    message = serializers.CharField(min_length=20)

    def save(self):
        request    = self.context.get('request')
        xff        = request.META.get('HTTP_X_FORWARDED_FOR') if request else None
        ip_address = xff.split(',')[0].strip() if xff else (request.META.get('REMOTE_ADDR') if request else None)
        
        return ContactMessage.objects.create(
            name = self.validated_data['name'],
            email = self.validated_data['email'].lower(),
            subject = self.validated_data['subject'],
            messages = self.validated_data['message'],
            ip_address=ip_address
        )


class HomepageDataSerializer(serializers.Serializer):
    """
    Master aggregator - returns every homepage section in a single response
    GET /home/
    Sections assembled in parallel-friendly dict structure.
    """

    def to_representation(self, user):
        now = timezone.now()

        # ── Banners ───────────────────────────────────────────────────────────
        hero_banners = [b for b in Banner.objects.filter(
            banner_type=Banner.HERO, is_active=True
            ).order_by('position')[:5] if b.is_live]
        
        promo_banners = [b for b in Banner.objects.filter(
            banner_type=Banner.PROMOTIONAL, is_active=True
            ).order_by('position')[:5] if b.is_live]
         
        # ── Featured products ─────────────────────────────────────────────────
        featured_qs = Product.objects.filter(is_active=True, is_featured=True).order_by('-sold_count')[:12]

        # ── Trending products ──────────────────────────────────────────────────
        trending_qs = Product.objects.filter(is_active=True).order_by('-view_count')[:8]

        # ── New arrivals ──────────────────────────────────────────────────────
        new_arrivals = Product.objects.filter(is_active=True).order_by('-created_at')[:8]

        # ── Best sellers ──────────────────────────────────────────────────────
        best_seller = Product.objects.filter(is_active=True).order_by('-sold_count')[:8]

        # ── Deals / flash sales ───────────────────────────────────────────────
        flash_sales = FlashSale.objects.filter(
            is_active=True, starts_at__lte=now, ends_at__gte=now
        ).order_by('-discount_percent')[:3]

        # ── Featured markets ──────────────────────────────────────────────────
        markets_qs = Market.objects.filter(is_active=True, is_verified=True).order_by('-total_sales')[:6]

        # ── Popular categories ─────────────────────────────────────────────────
        categories = Category.objects.filter(
            is_active=True, parent_id__isnull=True
        ).order_by('order_position')[:8]

        # ── Active promotions ─────────────────────────────────────────────────
        active_promos = Promotion.objects.filter(
            is_active=True, starts_at__lte=now, ends_at__gte=now
        ).order_by('-is_featured')[:4]

        # ── Popular searches ──────────────────────────────────────────────────
        popular_searches = PopularSearch.objects.order_by('-count')[:10]

        return {
            'hero': {
                'banners': BannerListSerializer(hero_banners, many=True).data,
                'toal_products': Product.objects.filter(is_active=True).count(),
                'total_markets': Market.objects.filter(is_active=True, is_verified=True).count(),
            },
            'promotional_banners': PromotionalBannerSerializer(promo_banners, many=True).data,
            'featured_products':   _ProductCardMini(featured_qs, many=True).data,
            'trending_products':   _ProductCardMini(trending_qs, many=True).data,
            'new_arrivals':        _ProductCardMini(new_arrivals, many=True).data,
            'best_sellers':        _ProductCardMini(best_seller, many=True).data,
            'featured_markets':    _MarketMini(markets_qs, many=True).data,
            'categories':          _CategoryMini(categories, many=True).data,
            'flash_sales': [
                {
                    'id':                sale.id,
                    'title':             sale.title,
                    'discount_percent':  str(sale.discount_percent),
                    'ends_at':           sale.ends_at,
                    'seconds_remaining': max(0, int((sale.ends_at - now).total_seconds())),
                    'products':          _ProductCardMini(sale.products.filter(is_active=True)[:4], many=True).data,
                }
                for sale in flash_sales
            ],
            'active_promotions': [
                {
                    'id':               p.id,
                    'title':            p.title,
                    'promo_type':       p.promo_type,
                    'discount_percent': str(p.discount_percent) if p.discount_percent else None,
                    'image_url':        p.image.url if p.image else None,
                    'ends_at':          p.ends_at,
                }
                for p in active_promos
            ],
            'popular_searches': [p.query for p in popular_searches],
            'generated_at':    now,
        }



# NAVIGATION

class NavigationCategoriesSerializer(serializers.ModelSerializer):
    """Top level categories for the main navigation bar."""
    subcategory_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'subcategory_count']
        read_only_fields = fields
    
    def get_subcategory_count(self, obj):
        return obj.Children.filter(is_active=True).count()


class MegaMenuSerializer(serializers.Serializer):
    """
    Complete mega - menu structure - categories with subcategories
    and top products per category. Cached-friendly single call.
    """

    def to_representation(self, instance):
        root_categories = Category.objects.filter(
            is_active=True, parent_id__isnull=True
        ).order_by('order_position')[:10]

        menu = []
        for cat in root_categories:
            subcats = cat.Children.filter(is_active=True).order_by('order_position')[:8]
            top_prods = Product.objects.filter(
                category=cat, is_active=True, is_featured=True
            ).order_by('-sold_count')[:4]

            menu.append({
                'id':       cat.id,
                'name':     cat.name,
                'slug':     cat.slug,
                'icon':     cat.icon,
                'subcategories': [
                    {'id': s.id, 'name': s.name, 'slug': s.slug, 'icon': s.icon}
                    for s in subcats
                ],
                'featured_products': _ProductCardMini(top_prods, many=True).data,
                'product_count': cat.products.filter(is_active=True).count(),
            })

        return {'menu': menu}


class QuickLinksSerializer(serializers.Serializer):
    """
    Quick-access links for the header (New Arrivals, Best Seller, etc.)
    Static + dynamic links assembled together.
    """

    def to_representation(self, instance):
        return {
            'links': [
                {'label': 'New Arrivals',   'url': '/products/new-arrivals/',   'icon': 'sparkles'},
                {'label': 'Best Sellers',   'url': '/products/best-sellers/',   'icon': 'fire'},
                {'label': 'Today\'s Deals', 'url': '/promotions/active/',       'icon': 'tag'},
                {'label': 'Flash Sales',    'url': '/promotions/flash-sales/',  'icon': 'bolt'},
                {'label': 'Top Rated',      'url': '/products/top-rated/',      'icon': 'star'},
            ]
        }


class FooterLinksSerializer(serializers.Serializer):
    """
    Footer navigation sections - Help, Company, Social.
    """

    def to_representation(self, instance):
        return {
            'company': [
                {'label': 'About Us',   'url': '/about/'},
                {'label': 'Careers',    'url': '/careers/'},
                {'label': 'Press',      'url': '/press/'},
                {'label': 'Blog',       'url': '/blog/'},
            ],
            'support': [
                {'label': 'Help Center',    'url': '/help/'},
                {'label': 'Contact Us',     'url': '/home/contact/'},
                {'label': 'Returns',        'url': '/returns/'},
                {'label': 'Order Status',   'url': '/orders/'},
            ],
            'legal': [
                {'label': 'Privacy Policy', 'url': '/privacy/'},
                {'label': 'Terms of Use',   'url': '/terms/'},
                {'label': 'Cookie Policy',  'url': '/cookies/'},
            ],
            'social': [
                {'platform': 'instagram',   'url': 'https://instagram.com/'},
                {'platform': 'twitter',     'url': 'https://twitter.com/'},
                {'platform': 'facebook',    'url': 'https://facebook.com/'},

            ]
        }


class BreadcrumbSerializer(serializers.Serializer):
    """
    Generates a breadcrumb trail from a bath string
    Input: { "path": "/products/categories/12/some-product/" }
    """
    path = serializers.CharField()

    def build(self) -> list:
        path = self.validated_data['path'].strip('/')
        parts = [p for p in path.split('/') if p]
        crumbs = [{'label': 'Home', 'url': '/'}]
        built = ''

        label_map = {
            'products':   'Products',
            'categories': 'Categories',
            'orders':     'Orders',
            'stores':     'Stores',
            'promotions': 'Promotions',
        }

        for part in parts:
            built += f'/{part}'
            label = label_map.get(part, part.replace('-', ' ').title())
            crumbs.append({'label': label, 'url': built + '/'})
        
        return crumbs



# GLOBAL SEARCH

class GlobalSearchSerializer(serializers.Serializer):
    """
    Searches across products, markets, and categories simultaneously.
    GET /home/search/?q=...&type=all|products|markets|categories
    """
    q = serializers.CharField(min_length=2)
    type = serializers.ChoiceField(
        choices=['all', 'products', 'markets', 'categories'],
        required=False,
        default='all',
    )
    limit = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)

    def search(self, user=None) -> dict:
        q = self.validated_data['q'].strip()
        scope = self.validated_data['type']
        limit = self.validated_data['limit']
        result = {}

        if scope in ('all', 'products'):
            prods = Product.objects.filter(
                is_active=True
            ).filter(
                Q(name__icontains=q) | Q(description__icontains=q) | Q(sku__icontains=q)
            ).order_by('-rating_average')[:limit]
            result['products'] = _ProductCardMini(prods, many=True).data
        
        if scope in ('all', 'markets'):
            markets = Market.objects.filter(
                is_active=True
            ).filter(
                Q(market_name__icontains=q) | Q(description__icontains=q)
            ).order_by('-rating_average')[:limit]
            result['markets'] = _MarketMini(markets, many=True).data
        
        if scope in ('all', 'categories'):
            cats = Category.objects.filter(
                is_active=True, name__icontains=q
            ).order_by('order_position')[:limit]
            result['categories'] = _CategoryMini(cats, many=True).data
        
        result['query'] = q
        result['total_count'] = sum(len(v) for v in result.values() if isinstance(v, list))

        # Record search
        if user and user.is_authenticated:
            SearchHistory.objects.create(user=user, query=q, result_count=result['total_count'])
        
        # Update popular searches
        obj, created = PopularSearch.objects.get_or_create(query=q.lower())
        if not created:
            PopularSearch.objects.filter(pk=obj.pk).update(count=obj.count + 1)
        
        return result


class SearchSuggestionsSerializer(serializers.Serializer):
    """
    Autocomplete suggestions - product names + popular searches matching the prefix.
    GET /home/search/suggestions/?q=...
    """

    q = serializers.CharField(min_length=1, max_length=100)

    def suggest(self) -> dict:
        q = self.validated_data['q'].strip()
        products = (
            Product.objects
            .filter(is_active=True, name__istartswith=q)
            .values_list('name', flat=True)
            .order_by('-sold_count')[:5]
        )
        popular = (
            PopularSearch.objects
            .filter(query__istartswith=q.lower())
            .values_list('query', flat=True)
            .order_by('-count')[:5]
        )
        categories = (
            Category.objects
            .filter(is_active=True, name__istartswith=q)
            .values_list('name', flat=True)[:3]
        )

        # Merge and deduplicate preserving order
        seen = set()
        suggestions = []
        for item in list(products) + list(popular) + list(categories):
            key = item.lower()
            if key not in seen:
                seen.add(key)
                suggestions.append(item)
        
        return {'query': q, 'suggestions': suggestions[:10]}


class SearchResultsSerializer(serializers.Serializer):
    """
    Unified search results page - products with filter sidebar data.
    GET /home/search/results/?q=...
    """

    q           = serializers.CharField(min_length=2)
    category    = serializers.IntegerField(required=False)
    min_price   = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    max_price   = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    min_rating  = serializers.DecimalField(required=False, max_digits=3, decimal_places=2)
    in_stock = serializers.BooleanField(required=False)
    sort = serializers.ChoiceField(
        required=False, default='relevance',
        choices=['relevance', 'price_asc', 'price_desc', 'rating', 'newest', 'popular'],
    )

    def get_results(self) -> dict:
        from django.db.models import Min, Max
        q = self.validated_data['q'].strip()
        qs = Product.objects.filter(
            is_active=True
        ).filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(sku__icontains=q)
        )

        if self.validated_data.get('category'):
            qs = qs.filter(category_id=self.validated_data['category'])
        if self.validated_data.get('min_price') is not None:
            qs = qs.filter(price__gte=self.validated_data['min_price'])
        if self.validated_data.get('max_price') is not None:
            qs = qs.filter(price__lte=self.validated_data['max_price'])
        if self.validated_data.get('min_rating') is not None:
            qs = qs.filter(rating_average__gte=self.validated_data['min_rating'])
        if self.validated_data.get('in_stock') is True:
            qs = qs.filter(stock_quantity__gt=0)
        
        sort_map = {
            'relevance':  '-sold_count',
            'price_asc':  'price',
            'price_desc': '-price',
            'rating':     '-rating_average',
            'newest':     '-created_at',
            'popular':    '-view_count',
        }

        qs = qs.order_by(sort_map.get(self.validated_data.get('sort', 'relevance'), '-sold_count'))

        price_range = qs.aggregate(min=Min('price'), max=Max('price'))
        categories = Category.objects.filter(
            products__in=qs
        ).annotate(count=Count('products')).order_by('-count')[:8]

        return {
            'query':       q,
            'total_count': qs.count(),
            'products':    _ProductCardMini(qs[:40], many=True).data,
            'price_range': {
                'min': str(price_range['min'] or 0),
                'max': str(price_range['max'] or 0)
            },
            'filter_categories': _CategoryMini(categories, many=True).data,
        }

class SearchHistorySerializer(serializers.ModelSerializer):
    """User's recent search history"""
    class Meta:
        model = SearchHistory
        fields = ['id', 'query', 'result_count', 'searched_at']
        read_only_fields = fields

class PopularSearchesSerializer(serializers.ModelSerializer):
    """GLobally trending search terms."""

    class Meta:
        model = PopularSearch
        fields = ['query', 'count']
        read_only_fields = fields

class SearchFiltersSerializer(serializers.Serializer):
    """
    Available filters for a given search result set.
    Returns price, range, categories, and sort options.
    """

    def to_representation(self, qs):
        from django.db.models import Min, Max
        price = qs.aggregate(min=Min('price'), max=Max('price'))
        cats = Category.objects.filter(
            product__in=qs
        ).annotate(count=Count('products')).order_by('-count')[:10]

        return {
            'price_range': {
                'min': str(price['min'] or 0),
                'max': str(price['max'] or 0),
            },
            'categories': _CategoryMini(cats, many=True).data,
            'sort_options': [
                {'value': 'relevance',  'label': 'Most Relevant'},
                {'value': 'price_asc',  'label': 'Price: Low to High'},
                {'value': 'price_desc', 'label': 'Price: High to Low'},
                {'value': 'rating',     'label': 'Highest Rated'},
                {'value': 'newest',     'label': 'Newest First'},
                {'value': 'popular',    'label': 'Most Popular'},
            ],
            'in_stock_count': qs.filter(stock_quantity__gt=0).count(),
        }

class PageViewSerializer(serializers.Serializer):
    """
    Tracks a page view.
    POST /home/analytics/page-view/
    Fires-and-forgets - always returns 200.
    """
    path = serializers.CharField(max_length=500)
    referrer = serializers.CharField(max_length=500, required=False, allow_blank=True)
    session_key = serializers.CharField(max_length=40, required=False, allow_blank=True)

    def save(self):
        request = self.context.get('request')
        xff        = request.META.get('HTTP_X_FORWARDED_FOR') if request else None
        ip_address = xff.split(',')[0].strip() if xff else (request.META.get('REMOTE_ADDR') if request else None)

        PageView.objects.create(
            user        = request.user if (request and request.user.is_authenticated) else None,
            path        = self.validated_data['path'],
            referrer    = self.validated_data.get('referrer', ''),
            session_key = self.validated_data.get('session_key', ''),
            ip_address  = ip_address,
            user_agent  = request.META.get('HTTP_USER_AGENT', '') if request else '',
        )
        
class ClickTrackingSerializer(serializers.Serializer):
    """
    Tracks a click on a product, banner, or link.
    POST /home/analytics/click/
    """
    category    = serializers.CharField(max_length=100)
    label       = serializers.CharField(max_length=255)
    value       = serializers.CharField(max_length=255, required=False, allow_blank=True)
    path        = serializers.CharField(max_length=500, required=False, allow_blank=True)
    session_key = serializers.CharField(max_length=40,  required=False, allow_blank=True)

    def save(self):
        request     = self.context.get('request')
        xff         = request.META.get('HTTP_X_FORWARDED_FOR') if request else None
        ip          = xff.split(',')[0].strip() if xff else (request.META.get('REMOTE_ADDR') if request else None)

        AnalyticsEvent.objects.create(
            user        = request.user if (request and request.user.is_authenticated) else None,
            event_type  = AnalyticsEvent.CLICK,
            category    = self.validated_data['category'],
            label       = self.validated_data['label'],
            value       = self.validated_data.get('value', ''),
            path        = self.validated_data.get('path', ''),
            session_key = self.validated_data.get('session_key', ''),
            ip_address  = ip,
        )

        # banner click => increment the banner click count
        if self.validated_data['category'] == 'banner':
            try:
                banner_id = int(self.validated_data['label'])
                Banner.objects.filter(pk=banner_id).update(click_count=Banner.objects.get(pk=banner_id).click_count + 1)
            except (ValueError, Banner.DoesNotExist):
                pass


class UserActivityLogSerializer(serializers.Serializer):
    """
    Logs a structured user activity (add_to_cart, purchase, searc, etc)
    POST /home/analytics/activity/
    """
    event_type  = serializers.ChoiceField(choices=AnalyticsEvent.EVENT_TYPES)
    category    = serializers.CharField(max_length=100, required=False, allow_blank=True)
    label       = serializers.CharField(max_length=255, required=False, allow_blank=True)
    value       = serializers.CharField(max_length=255, required=False, allow_blank=True)
    path        = serializers.CharField(max_length=500, required=False, allow_blank=True)
    session_key = serializers.CharField(max_length=40,  required=False, allow_blank=True)
    metadata    = serializers.DictField(required=False, allow_null=True)

    def save(self, **kwargs):
        request = self.context.get('request')
        xff     = request.META.get('HTTP_X_FORWARDED_FOR') if request else None
        ip      = xff.split(',')[0].strip() if xff else (request.META.get('REMOTE_ADDR') if request else None)

        AnalyticsEvent.objects.create(
            user        = request.user if (request and request.user.is_authenticated) else None,
            event_type  = self.validated_data['event_type'],
            category    = self.validated_data.get('category', ''),
            label       = self.validated_data.get('label', ''),
            value       = self.validated_data.get('value', ''),
            path        = self.validated_data.get('path', ''),
            session_key = self.validated_data.get('session_key', ''),
            ip_address  = ip,
            metadata = self.validated_data.get('metadata'),
        )

class AnalyticsEventSerializer(serializers.Serializer):
    """
    Generic analytics event recoder.
    POST /home/analytics/event/
    Accepts any event_type with optional metadata dict
    """
    event_type  = serializers.ChoiceField(choices=AnalyticsEvent.EVENT_TYPES)
    category    = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    label       = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    value       = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    path        = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')
    session_key = serializers.CharField(max_length=40,  required=False, allow_blank=True, default='')
    metadata    = serializers.DictField(required=False, allow_null=True)

    def save(self, **kwargs):
        request = self.context.get('request')
        xff     = request.META.get('HTTP_X_FORWARDED_FOR') if request else None
        ip      = xff.split(',')[0].strip() if xff else (request.META.get('REMOTE_ADDR') if request else None)

        AnalyticsEvent.objects.create(
            user        = request.user if (request and request.user.is_authenticated) else None,
            event_type  = self.validated_data['event_type'],
            category    = self.validated_data['category'],
            label       = self.validated_data['label'],
            value       = self.validated_data['value'],
            path        = self.validated_data['path'],
            session_key = self.validated_data['session_key'],
            ip_address  = ip,
            metadata = self.validated_data.get('metadata'),
        )