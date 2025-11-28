from django.db import models

class Report(models.Model):
    REGION_CHOICES = [
        ("car", "CAR"),
        ("central", "Central Office"),
        ("ncr", "NCR"),
        ("negros", "Negros Island Region"),
        ("1", "Region I"),
        ("2", "Region II"),
        ("3", "Region III"),
        ("4.1", "Region IV-A"),
        ("4.2", "Region IV-B"),
        ("5", "Region V"),
        ("6", "Region VI"),
        ("7", "Region VII"),
        ("8", "Region VIII"),
        ("9", "Region IX"),
        ("10", "Region X"),
        ("11", "Region XI"),
        ("12", "Region XII"),
        ("13", "Region XIII"),
    ]

    STATUS_CHOICES = [
        ("complete", "Complete"),
        ("incomplete", "Incomplete"),
    ]

    region = models.CharField(max_length=20, choices=REGION_CHOICES)
    latitude = models.DecimalField(max_digits=50, decimal_places=20)  # Changed from CharField
    longitude = models.DecimalField(max_digits=50, decimal_places=20)  # Changed from CharField
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)  # Added choices
    description = models.CharField(max_length=120, blank=True)
    photo = models.ImageField(upload_to="reports/")

    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Region: {self.get_region_display()} | "
            f"Status: {self.get_status_display()} | "
            f"Latitude: {self.latitude} | "
            f"Longitude: {self.longitude} | "
            f"Description: {self.description or 'N/A'} | "
            f"Approved: {'Yes' if self.approved else 'No'} | "
            f"Created At: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )   

class Meta:
        ordering = ['-created_at']
        verbose_name = "Report"
        verbose_name_plural = "Reports"