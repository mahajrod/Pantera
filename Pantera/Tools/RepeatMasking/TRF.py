#!/usr/bin/env python
__author__ = 'Sergei F. Kliver'

import os
import shutil

from Pantera.Tools.Abstract import Tool

from Pantera.Parsers.TRF import CollectionTRF
from Pantera.Routines import FileRoutines
from Pantera.Tools.LinuxTools import CGAS


class TRF(Tool):
    def __init__(self, path="", max_threads=4):
        Tool.__init__(self, "trf", path=path, max_threads=max_threads)

    @staticmethod
    def parse_common_options(matching_weight=2, mismatching_penalty=7, indel_penalty=7,
                             match_probability=80, indel_probability=10, min_alignment_score=50, max_period=500,
                             report_flanking_sequences=False, make_dat_file=True):

        options = " %i" % matching_weight
        options += " %i" % mismatching_penalty
        options += " %i" % indel_penalty
        options += " %i" % match_probability
        options += " %i" % indel_probability
        options += " %i" % min_alignment_score
        options += " %i" % max_period
        options += " -f" if report_flanking_sequences else ""
        options += " -d" if make_dat_file else ""

        return options

    def search_tandem_repeats(self, query_file, matching_weight=2, mismatching_penalty=7, indel_penalty=7,
                              match_probability=80, indel_probability=10, min_alignment_score=50, max_period=500,
                              report_flanking_sequences=False, make_dat_file=True, disable_html_output=True):

        options = " %s" % query_file
        options += self.parse_common_options(matching_weight=matching_weight, mismatching_penalty=mismatching_penalty,
                                             indel_penalty=indel_penalty, match_probability=match_probability,
                                             indel_probability=indel_probability, min_alignment_score=min_alignment_score,
                                             max_period=max_period, report_flanking_sequences=report_flanking_sequences,
                                             make_dat_file=make_dat_file)

        options += " -h" if disable_html_output else ""

        self.execute(options)

    @staticmethod
    def convert_trf_report(trf_report, output_prefix):

        trf_collection = CollectionTRF(trf_file=trf_report, from_file=True)

        trf_collection.write("%s.rep" % output_prefix)
        trf_collection.write_gff("%s.gff" % output_prefix)
        trf_collection.write_simple_gff("%s.simple.gff" % output_prefix)
        trf_collection.write_short_table("%s.short.tab" % output_prefix)
        trf_collection.write_wide_table("%s.wide.tab" % output_prefix)

    def parallel_search_tandem_repeat(self, query_file, output_prefix, matching_weight=2, mismatching_penalty=7,
                                      indel_penalty=7,
                                      match_probability=80, indel_probability=10, min_alignment_score=50, max_period=500,
                                      report_flanking_sequences=False, splited_fasta_dir="splited_fasta_dir",
                                      splited_result_dir="splited_output", converted_output_dir="converted_output",
                                      max_len_per_file=100000, store_intermediate_files=False):
        work_dir = os.getcwd()
        splited_filename = FileRoutines.split_filename(query_file)
        self.split_fasta_by_seq_len(query_file, splited_fasta_dir, max_len_per_file=max_len_per_file,
                                    output_prefix=splited_filename[1])

        common_options = self.parse_common_options(matching_weight=matching_weight,
                                                   mismatching_penalty=mismatching_penalty,
                                                   indel_penalty=indel_penalty, match_probability=match_probability,
                                                   indel_probability=indel_probability,
                                                   min_alignment_score=min_alignment_score,
                                                   max_period=max_period,
                                                   report_flanking_sequences=report_flanking_sequences,
                                                   make_dat_file=True)
        common_options += " -h"  # suppress html output
        options_list = []
        splited_files = os.listdir(splited_fasta_dir)

        FileRoutines.safe_mkdir(splited_result_dir)
        FileRoutines.safe_mkdir(converted_output_dir)
        os.chdir(splited_result_dir)

        input_dir = splited_fasta_dir if (splited_fasta_dir[0] == "/") or (splited_fasta_dir[0] == "~") \
                    else "../%s" % splited_fasta_dir

        for filename in splited_files:
            file_options = "%s/%s" % (input_dir, filename)
            file_options += common_options
            options_list.append(file_options)

        self.parallel_execute(options_list)

        os.chdir(work_dir)
        for filename in splited_files:

            trf_output_file = "%s/%s.%i.%i.%i.%i.%i.%i.%i.dat" % (splited_result_dir, filename,
                                                                  matching_weight, mismatching_penalty,
                                                                  indel_penalty, match_probability,
                                                                  indel_probability,
                                                                  min_alignment_score, max_period)

            self.convert_trf_report(trf_output_file, "%s/%s" % (converted_output_dir, filename))

        for suffix in (".rep", ".gff", ".simple.gff", ".short.tab", ".wide.tab"):
            file_str = ""
            merged_file = "%s%s" % (output_prefix, suffix)
            for filename in splited_files:
                file_str += " %s/%s%s" % (converted_output_dir, filename, suffix)
            CGAS.cat(file_str, merged_file)

        if not store_intermediate_files:
            shutil.rmtree(splited_fasta_dir)
            shutil.rmtree(splited_result_dir)
            shutil.rmtree(converted_output_dir)

if __name__ == "__main__":
    pass
