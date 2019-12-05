import uuid
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .utils.network.client import ping


class NetworkLocation(models.Model):
    """
    ``NetworkLocation`` stores information about a network address through which an instance of Kolibri can be accessed,
    which can be used to sync content or data.
    """

    EXPIRATION_TIMEDELTA = timedelta(seconds=10)
    DEFAULT_PING_TIMEOUT_SECONDS = 5

    class Meta:
        ordering = ["added"]

    # for statically added network locations: `id` will be a random UUID
    # for dynamically discovered devices: `id` will be the device's `instance_id`
    id = models.CharField(
        primary_key=True, max_length=36, default=uuid.uuid4, editable=False
    )
    base_url = models.CharField(max_length=100)

    application = models.CharField(max_length=32, blank=True)
    kolibri_version = models.CharField(max_length=100, blank=True)
    instance_id = models.CharField(max_length=32, blank=True)
    device_name = models.CharField(max_length=100, blank=True)
    operating_system = models.CharField(max_length=32, blank=True)

    added = models.DateTimeField(auto_now_add=True, db_index=True)
    last_accessed = models.DateTimeField(auto_now=True)
    last_available = models.DateTimeField(null=True)
    last_unavailable = models.DateTimeField(null=True)

    dynamic = models.BooleanField(default=False)

    def ping(self):
        info = ping(self.base_url, timeout=self.DEFAULT_PING_TIMEOUT_SECONDS)
        now = timezone.now()
        if info:
            self.update(last_available=now, **info)
            return info
        else:
            self.update(last_unavilable=now)
            return None

    @property
    def available(self):
        """
        If this connection was checked recently, report that result,
        otherwise do a fresh check.
        """
        expiration_time = timezone.now() - self.EXPIRATION_TIMEDELTA

        available_recently = self.last_available > expiration_time
        unavailable_recently = self.last_unavailable > expiration_time

        is_available = (
            available_recently and self.last_available > self.last_unavailable
        )

        if is_available:
            return True
        elif unavailable_recently:
            return False
        else:
            return True if self.ping() else False


class StaticNetworkLocationManager(models.Manager):
    def get_queryset(self):
        queryset = super(StaticNetworkLocationManager, self).get_queryset()
        return queryset.filter(dynamic=False)


class StaticNetworkLocation(NetworkLocation):
    objects = StaticNetworkLocationManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.dynamic = False
        return super(StaticNetworkLocation, self).save(*args, **kwargs)


class DynamicNetworkLocationManager(models.Manager):
    def get_queryset(self):
        queryset = super(DynamicNetworkLocationManager, self).get_queryset()
        return queryset.filter(dynamic=True)

    def purge(self):
        self.get_queryset().delete()

    def log_location(self, base_url, **kwargs):
        info = ping(base_url)
        if info:
            instance_id = info.get("instance_id")
            info.update(last_available=timezone.now())
            location, created = self.update_or_create(info, id=instance_id)
            return location


class DynamicNetworkLocation(NetworkLocation):
    objects = DynamicNetworkLocationManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.dynamic = True

        if self.id and self.instance_id and self.id != self.instance_id:
            raise ValidationError(
                {"instance_id": "`instance_id` and `id` must be the same"}
            )

        if self.instance_id:
            return super(DynamicNetworkLocation, self).save(*args, **kwargs)
        else:
            raise ValidationError(
                {
                    "instance_id": "DynamicNetworkLocations must be be created with an instance ID!"
                }
            )
