from io import StringIO

from dateutil.relativedelta import relativedelta
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from flows.models import Flow, FlowQuestion, FlowResponse


class DeleteHistoricalRecordsTests(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "delete_historical_flowresponses",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def create_record(self, id, timestamp):
        question = FlowQuestion.objects.create(flow=Flow.objects.create())
        record = FlowResponse.objects.create(
            id=id,
            question=question,
            flow=question.flow,
            row_id_type=FlowResponse.Type.STRING,
            contact_id_type=FlowResponse.Type.STRING,
            contact_id_value={},
            session_id_type=FlowResponse.Type.STRING,
            session_id_value={},
            response_type=FlowResponse.Type.STRING,
            response_value={},
            response_metadata={},
        )
        record.timestamp = timestamp
        record.save()

    def test_missing_arguments(self):
        self.assertRaises(CommandError, self.call_command)

    def test_delete_flowresponses(self):
        running_month = timezone.now() - relativedelta(months=12, hour=12)

        for i in range(12):
            self.create_record(i, running_month)
            running_month = running_month + relativedelta(months=1)

        self.call_command(6)

        self.assertEqual(FlowResponse.objects.count(), 6)
