from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
import uuid
from .google_drive_utils import extract_google_drive_id, get_google_drive_direct_url

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    objects = CustomUserManager()
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('ORGANIZER', 'Organizer'),
        ('VOLUNTEER', 'Volunteer'),
        ('CUSTOMER', 'Customer'),
    )

    username = None
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CUSTOMER')
    mobile_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verification_otp = models.CharField(max_length=6, blank=True, null=True)
    email_verification_otp_created_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

from django.utils.text import slugify

class Event(models.Model):
    EVENT_STATUS = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('CANCELLED', 'Cancelled'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    event_type = models.CharField(max_length=100)  # Free text field for event type
    short_description = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=200)
    venue_address = models.TextField(blank=True)
    venue_map_link = models.URLField(blank=True)
    capacity = models.PositiveIntegerField()
    registration_deadline = models.DateTimeField(null=True, blank=True)
    registration_start_date = models.DateTimeField(null=True, blank=True, help_text="When ticket sales begin")
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    status = models.CharField(max_length=10, choices=EVENT_STATUS, default='DRAFT')
    banner_image_url = models.TextField(blank=True, help_text="Google Drive shareable link or iframe code for banner image")
    banner_image_id = models.CharField(max_length=200, blank=True, help_text="Extracted Google Drive file ID")
    banner_image = models.ImageField(upload_to='event_banners/', null=True, blank=True)  # Keep for backward compatibility
    featured = models.BooleanField(default=False)
    venue_terms = models.TextField(blank=True)
    event_terms = models.TextField(blank=True)
    restrictions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Extract Google Drive ID from banner URL if provided
        if self.banner_image_url and not self.banner_image_id:
            self.banner_image_id = extract_google_drive_id(self.banner_image_url)
        super().save(*args, **kwargs)
    
    def get_banner_image_url(self):
        """Get the direct viewable URL for Google Drive image"""
        if self.banner_image_id:
            return get_google_drive_direct_url(self.banner_image_id)
        elif self.banner_image:
            return self.banner_image.url
        return None
    
    def __str__(self):
        return self.title
        
    @property
    def total_attendees_capacity(self):
        return self.capacity
        
    @property
    def total_tickets_sold(self):
        return self.tickets.filter(status='SOLD').count()
        
    @property
    def total_attendees_registered(self):
        sold_tickets = self.tickets.filter(status='SOLD').select_related('ticket_type')
        return sum(ticket.ticket_type.attendees_per_ticket for ticket in sold_tickets)
    
    @property
    def remaining_attendee_capacity(self):
        return self.capacity - self.total_attendees_registered
    
    @property
    def tickets_are_live(self):
        """Check if ticket sales have started"""
        from django.utils import timezone
        now = timezone.now()
        
        # If no registration start date is set, tickets are live
        if not self.registration_start_date:
            return True
        
        # Check if current time is after registration start date
        return now >= self.registration_start_date
    
    def __str__(self):
        return self.title

class EventSponsor(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sponsors')
    sponsor_name = models.CharField(max_length=200)
    logo_url = models.TextField(help_text="Google Drive shareable link or iframe code for sponsor logo")
    logo_id = models.CharField(max_length=200, blank=True, help_text="Extracted Google Drive file ID")
    website_url = models.URLField(blank=True, help_text="Sponsor's website URL")
    sponsor_type = models.CharField(max_length=100, blank=True, help_text="Type of sponsorship (e.g., Ticketing Partner, Gold Sponsor, Venue Partner)")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers appear first)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'sponsor_name']
    
    def save(self, *args, **kwargs):
        # Extract Google Drive ID from logo URL
        if self.logo_url and not self.logo_id:
            self.logo_id = extract_google_drive_id(self.logo_url)
        super().save(*args, **kwargs)
    
    def get_logo_url(self):
        """Get the direct viewable URL for Google Drive logo"""
        if self.logo_id:
            return get_google_drive_direct_url(self.logo_id)
        elif self.logo_url:
            # Extract ID from URL if not already stored
            file_id = extract_google_drive_id(self.logo_url)
            if file_id:
                return get_google_drive_direct_url(file_id)
        return None
    
    def __str__(self):
        return f"{self.sponsor_name} - {self.event.title}"

class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
    type_name = models.CharField(max_length=100)  # Free text field for ticket type
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    attendees_per_ticket = models.PositiveIntegerField(default=1, help_text="Number of attendees allowed per ticket (e.g., 2 for couple tickets)")
    
    def __str__(self):
        return f"{self.type_name} - {self.event.title}"
    
    @property
    def total_attendees_capacity(self):
        return self.quantity * self.attendees_per_ticket

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('RESERVED', 'Reserved'),
        ('SOLD', 'Sold'),
        ('VALID', 'Valid'),
        ('USED', 'Used'),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='tickets', null=True, blank=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets', null=True, blank=True)
    ticket_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='AVAILABLE')
    purchase_date = models.DateTimeField(null=True, blank=True)
    unique_secure_token = models.CharField(max_length=100, null=True, blank=True, unique=True)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_tickets')
    purchase_transaction = models.ForeignKey('PaymentTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    
    # New fields for consolidated tickets
    total_admission_count = models.IntegerField(default=1, help_text="Total number of people this ticket admits")
    booking_quantity = models.IntegerField(default=1, help_text="Number of tickets booked to create this consolidated ticket")
    
    def __str__(self):
        return f"{self.ticket_number} - {self.event.title}"

class PaymentTransaction(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('CREATED', 'Created'),
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    order_id = models.CharField(max_length=100, unique=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    cf_payment_id = models.CharField(max_length=100, null=True, blank=True)  # Cashfree payment ID
    payment_gateway = models.CharField(max_length=50, default="Cashfree")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='CREATED')
    payment_status = models.CharField(max_length=20, default='Pending')  # For webhook compatibility
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)  # Associated event
    quantity = models.PositiveIntegerField(default=1)  # Number of tickets
    response_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.order_id} - {self.get_status_display()}"


class PromoCode(models.Model):
    DISCOUNT_TYPE = (
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
    )
    
    code = models.CharField(max_length=20, unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='promo_codes')
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=0)  # 0 means unlimited
    current_uses = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} - {self.event.title}"
        
    @property
    def is_valid(self):
        import logging
        from django.utils import timezone
        now = timezone.now()
        logging.debug(f"PromoCode.is_valid check: is_active={self.is_active}, valid_from={self.valid_from}, valid_until={self.valid_until}, now={now}, max_uses={self.max_uses}, current_uses={self.current_uses}")
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.max_uses == 0 or self.current_uses < self.max_uses)
        )
        
    def total_tickets_booked(self):
        """Return the total number of tickets booked using this promo code (only successful, non-sandbox transactions)"""
        successful_usages = self.promo_code_usages.filter(
            ticket__purchase_transaction__status='SUCCESS'
        ).exclude(
            ticket__purchase_transaction__payment_gateway='SANDBOX'
        )
        return successful_usages.count()
        
    def total_amount_saved(self):
        """Return the total amount saved using this promo code (only successful, non-sandbox transactions)"""
        from django.db.models import Sum
        successful_usages = self.promo_code_usages.filter(
            ticket__purchase_transaction__status='SUCCESS'
        ).exclude(
            ticket__purchase_transaction__payment_gateway='SANDBOX'
        )
        result = successful_usages.aggregate(total=Sum('discount_amount'))
        return result['total'] or 0
        
    def redemption_rate(self):
        """Return the redemption rate as a percentage (based on successful transactions only)"""
        if self.max_uses == 0:
            return 100  # Unlimited codes are always considered 100% redeemable
        successful_uses = self.total_tickets_booked()  # This now filters for successful transactions
        return (successful_uses / self.max_uses) * 100 if self.max_uses > 0 else 0
        
    def total_revenue_generated(self):
        """Return the total revenue generated from tickets purchased with this promo code (only successful, non-sandbox transactions)"""
        from django.db.models import Sum
        successful_usages = self.promo_code_usages.filter(
            ticket__purchase_transaction__status='SUCCESS'
        ).exclude(
            ticket__purchase_transaction__payment_gateway='SANDBOX'
        )
        result = successful_usages.aggregate(total=Sum('order_total'))
        return result['total'] or 0
        
    def average_order_value(self):
        """Return the average order value for transactions using this promo code (only successful, non-sandbox transactions)"""
        from django.db.models import Avg
        successful_usages = self.promo_code_usages.filter(
            ticket__purchase_transaction__status='SUCCESS'
        ).exclude(
            ticket__purchase_transaction__payment_gateway='SANDBOX'
        )
        result = successful_usages.aggregate(avg=Avg('order_total'))
        return result['avg'] or 0
    
    def sync_current_uses(self):
        """Sync current_uses to match actual successful, non-sandbox usages"""
        actual_uses = self.total_tickets_booked()  # This now counts only successful transactions
        if self.current_uses != actual_uses:
            self.current_uses = actual_uses
            self.save(update_fields=['current_uses'])
        return actual_uses

class PromoCodeUsage(models.Model):
    """Track usage of promo codes for analytics"""
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name='promo_code_usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, null=True, blank=True)
    order_total = models.DecimalField(max_digits=10, decimal_places=2)  # Total before discount
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Actual discount applied
    used_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.promo_code.code} used by {self.user.email}"

class EventStaff(models.Model):
    STAFF_ROLE = (
        ('VOLUNTEER', 'Volunteer'),
        ('ORGANIZER', 'Organizer'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_staff_roles')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='staff')
    role = models.CharField(max_length=10, choices=STAFF_ROLE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('user', 'event', 'role')
        
    def __str__(self):
        return f"{self.user.email} - {self.event.title} ({self.role})"

class TicketPurchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_purchases')
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='purchases')
    purchase_date = models.DateTimeField(auto_now_add=True)
    payment_transaction = models.ForeignKey('PaymentTransaction', on_delete=models.SET_NULL, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='COMPLETED')

    def __str__(self):
        return f"{self.user.email} - {self.ticket.ticket_number} ({self.status})"


class EventCommission(models.Model):
    """Model to track commission settings for events"""
    COMMISSION_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='commission_settings')
    commission_type = models.CharField(max_length=10, choices=COMMISSION_TYPE_CHOICES, default='percentage')
    commission_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='commission_settings')

    def __str__(self):
        return f"{self.event.title} - {self.commission_type} commission: {self.commission_value}"
    
    def calculate_commission(self, total_price, attendee_count=1):
        """
        Calculate the commission amount based on the commission type and value.
        For fixed commissions, the fee is calculated per attendee.
        For percentage commissions, it's a percentage of the total price.
        """
        if self.commission_type == 'percentage':
            return round(float(total_price) * (float(self.commission_value) / 100), 2)
        else:  # fixed commission - calculated per attendee
            return float(self.commission_value) * attendee_count


class Invoice(models.Model):
    """Model to store invoice data for ticket purchases"""
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='invoice')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invoices')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='invoices')
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name='invoices')
    
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    invoice_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Ensure each ticket can only have one invoice
        unique_together = ['ticket', 'transaction']
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.ticket.ticket_number}"
    
    def save(self, *args, **kwargs):
        # Generate a unique invoice number if not provided
        if not self.invoice_number:
            import uuid
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)