from datetime import timedelta
import time
from django.test import TestCase
from utils.models import Constant

def _format_execution_time(self, execution_time):
    execution_str = ""

    if execution_time.total_seconds() < 1:
        milliseconds = execution_time.microseconds // 1000
        execution_str = f"{milliseconds} мс"
    elif execution_time.total_seconds() < 60:
        seconds = int(execution_time.total_seconds())
        execution_str = f"{seconds} с"
    else:
        minutes = int(execution_time.total_seconds() // 60)
        seconds = int(execution_time.total_seconds() % 60)
        execution_str = f"{minutes} мин {seconds} с"

    return execution_str

def test_run_get(count):
    for _ in range(count):  # arbitrary number of iterations
        obj = Constant.objects.get(code="text_const")
    return True



def test_run_filter_first(count):
    for _ in range(count):  # arbitrary number of iterations
        obj = Constant.objects.filter(code="text_const").first()
    return True


class StressTestCase(TestCase):
    def setUp(self):
        Constant.objects.create(code="text_const", value="text_const_value")

    def run_1(self):
        print("Через get")
        self.assertTrue(test_run_get(10000))

    def run_2(self):
        print("Через filter_first")
        self.assertTrue(test_run_filter_first(10000))