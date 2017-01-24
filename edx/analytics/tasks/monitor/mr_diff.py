import luigi
import os
import logging
import collections
import json

from edx.analytics.tasks.common.mapreduce import MapReduceJobTask, MultiOutputMapReduceJobTask
from edx.analytics.tasks.util.url import ExternalURL, get_target_from_url
from edx.analytics.tasks.util.url import url_path_join, ExternalURL, get_target_from_url
import edx.analytics.tasks.util.opaque_key_util as opaque_key_util

log = logging.getLogger(__name__)


class MapReduceDiff(MapReduceJobTask):

    output_root = luigi.Parameter()
    base_directory = luigi.Parameter()
    target_directory = luigi.Parameter()
    primary_key_columns = luigi.Parameter(is_list=True)

    def requires(self):
        yield ExternalURL(url=self.base_directory)
        yield ExternalURL(url=self.target_directory)

    def mapper(self, line):
        columns = line.split('\t')
        key = tuple([columns[int(column_index)] for column_index in self.primary_key_columns])
        values = []
        for i in xrange(len(columns)):
            if i not in self.primary_key_columns:
                values.append(columns[i])

        input_file = os.environ['mapreduce_map_input_file']
        values.append(input_file)
        yield key, tuple(values)

    def reducer(self, key, values):

        rows_in_base = []
        rows_in_target = []
        for value in values:
            map_file_name = value[-1]
            dirname = os.path.dirname(map_file_name)
            if dirname == os.path.dirname(self.base_directory):
                rows_in_base.append(value[:-1])
            elif dirname == os.path.dirname(self.target_directory):
                rows_in_target.append(value[:-1])

        base_values = []
        target_values = []

        base_collection = collections.Counter(rows_in_base)
        target_collection = collections.Counter(rows_in_target)

        if not base_collection == target_collection:
            base_collection.subtract(target_collection)
            for k, v in target_collection.iteritems():
                if v < 0:
                    for _ in range(abs(v)):
                        target_values.append(k)
                elif v > 0:
                    for _ in range(v):
                        base_values.append(k)

            output_json = {
                            'key': key,
                            'data': {
                                'base': base_values,
                                'target': target_values
                            }
                        }

            yield json.dumps(output_json)

        else:
            return

    def output(self):
        return get_target_from_url(self.output_root)
