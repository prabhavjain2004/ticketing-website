from django.db import models
from django.utils import timezone

class EventCommission(models.Model):
    """Model to track commission settings for events"""
    COMMISSION_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )

    event = models.OneToOneField('Event', on_delete=models.CASCADE, related_name='commission_settings')
    commission_type = models.CharField(max_length=10, choices=COMMISSION_TYPE_CHOICES, default='percentage')
    commission_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='commission_settings')

    def __str__(self):
        return f"{self.event.title} - {self.commission_type} commission: {self.commission_value}"
    
    def calculate_commission(self, total_price, attendee_count=1):
        """
        Calculate the commission amount based on the commission type and value.
        For fixed commission, it's calculated per attendee.
        For percentage commission, it's calculated on total price.
        """
        if self.commission_type == 'percentage':
            return round(float(total_price) * (float(self.commission_value) / 100), 2)
        else:  # fixed commission - calculated per attendee
            return float(self.commission_value) * attendee_count


class Invoice(models.Model):
    """Model to store invoice data for ticket purchases"""
    ticket = models.OneToOneField('Ticket', on_delete=models.CASCADE, related_name='invoice')
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='invoices')
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='invoices')
    ticket_type = models.ForeignKey('TicketType', on_delete=models.CASCADE, related_name='invoices')
    transaction = models.ForeignKey('PaymentTransaction', on_delete=models.CASCADE, related_name='invoices')
    
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
