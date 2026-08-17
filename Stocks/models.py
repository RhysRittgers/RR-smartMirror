from django.db import models
from django.contrib.auth.models import User
class StockPreference(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="stock_preferences"
    )

    symbol = models.CharField(max_length=10)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "symbol"],
                name="unique_user_stock_symbol"
            )
        ]

    def save(self, *args, **kwargs):
        self.symbol = self.symbol.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}: {self.symbol}"
    
class StockAlert(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="stock_alerts"
    )

    symbol = models.CharField(max_length=10)

    target_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    direction = models.CharField(
        max_length=10,
        choices=[
            ("above", "Above"),
            ("below", "Below"),
        ]
    )

    triggered = models.BooleanField(default=False)