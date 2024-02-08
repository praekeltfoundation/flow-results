import logging

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from flows.models import FlowResponse

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "retention_period",
            type=int,
            help="Specify the retention period in months",
            default=60,
        )

    def handle(self, *args, **options):
        retention_period = options["retention_period"]
        filter_date = timezone.now() - relativedelta(months=retention_period, hour=0)
        count, _ = FlowResponse.objects.filter(timestamp__lt=filter_date).delete()
        logger.info(f"Deleted {count} FlowResponse(s)")
