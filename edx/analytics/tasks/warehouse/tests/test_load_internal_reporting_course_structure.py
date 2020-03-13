"""Test active users computation"""

from datetime import datetime
import tempfile
from unittest import TestCase

from edx.analytics.tasks.warehouse.load_internal_reporting_course_structure import (
    LoadInternalReportingCourseStructureToMysqlTask
)


class TestLoadInternalReportingCourseStructureToMysqlTask(TestCase):
    """
    """
    def setUp(self):
        super(TestLoadInternalReportingCourseStructureToMysqlTask, self).setUp()
        self.temp_rootdir = tempfile.mkdtemp()

    def test_query(self):
        expected_columns = ('zzzzz',)
        import_task = LoadInternalReportingCourseStructureToMysqlTask(
            date=datetime(2017, 1, 1), warehouse_path=self.temp_rootdir
        )
        select_clause = import_task.insert_source_task.query().partition('FROM')[0]
        for column in expected_columns:
            assert column in select_clause
