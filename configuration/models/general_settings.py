from django.db import models


class GeneralSetting(models.Model):
    checking_period = models.PositiveIntegerField(default=30, verbose_name="Places checking period (1 to 500 days)")

    class Meta:
        verbose_name_plural = "General Settings"

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f'checking_period: {self.checking_period} day(s)'
