import os
import stat
import sys
import optparse
import logging
import shutil
import subprocess
import resource

class Stats:
    PARSING_TIME="parsing"
    SPEC_GROUNDING_TIME="spec_grounding"
    ENCODING_TIME="encoding"
    VERIFICATION_TIME="verification"
    SIMULATION_TIME="simulation"

    global_stats = None
    @staticmethod
    def get_global_stats():
        if Stats.global_stats is None:
            Stats.global_stats = Stats()
        return Stats.global_stats

    @staticmethod
    def reset_global():
        s = get_global_stats()
        s.reset()

    def __init__(self):
        self.start_times = {}
        self.end_times = {}

    def _diff_times(self, start_time, end_time):
        diff_list = []
        assert (len(end_time) == len(start_time))
        for (t1,t2) in zip(end_time, start_time):
            diff_list.append(t1 - t2)
        return diff_list

    def start_timer(self, timer_name, is_sub=False):
        assert timer_name not in self.start_times
        if not is_sub:
            start_times = os.times()
            self.start_times[timer_name] = start_times
        else:
            info = resource.getrusage(resource.RUSAGE_CHILDREN)
            self.start_times[timer_name] = (info.ru_utime, info.ru_stime)

    def stop_timer(self, timer_name, is_sub=False):
        assert timer_name in self.start_times
        assert timer_name not in self.end_times
        if not is_sub:
            end_times = os.times()
            self.end_times[timer_name] = end_times
        else:
            info = resource.getrusage(resource.RUSAGE_CHILDREN)
            end_times = (info.ru_utime, info.ru_stime)
            self.end_times[timer_name] = end_times

    def remove_timer(self, timer_name):
        if timer_name in self.start_times:
            self.start_times.pop(timer_name)
        if timer_name in self.end_times:
            self.end_times.pop(timer_name)

    def write_times(self, stream, timer_name):
        assert timer_name in self.start_times
        assert timer_name in self.end_times

        time_tuple = self._diff_times(self.start_times[timer_name],
                                      self.end_times[timer_name])

        stream.write("%s - User time: %f\n" % (timer_name, time_tuple[0]))
        stream.write("%s - System time: %f\n" % (timer_name, time_tuple[1]))
        stream.flush()

    def reset(self):
        self.global_stats = Stats()

