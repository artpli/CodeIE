#!/usr/bin/env python
# -*- coding:utf-8 -*-

# spot_prompt = '<spot>'
# asoc_prompt = '<asoc>'
#
# type_start = '<extra_id_0>'
# type_end = '<extra_id_1>'
# text_start = '<extra_id_2>'
# span_start = '<extra_id_5>'
# null_span = '<extra_id_6>'
# null_label = '<extra_id_7>'
#
#
# class StructureMarker:
#     def __init__(self) -> None:
#         pass
#
#
# class BaseStructureMarker(StructureMarker):
#     def __init__(self) -> None:
#         super().__init__()
#         self.sent_start = '<extra_id_0>'
#         self.sent_end = '<extra_id_1>'
#         self.record_start = '<extra_id_0>'
#         self.record_end = '<extra_id_1>'
#         self.span_start = '<extra_id_0>'
#         self.span_end = '<extra_id_1>'
#         self.text_start = '<extra_id_2>'
#         self.source_span_start = '<extra_id_3>'
#         self.source_span_end = '<extra_id_4>'
#         self.target_span_start = '<extra_id_5>'
#         self.null_span = '<extra_id_6>'
#         self.null_label = '<extra_id_7>'
#


spot_prompt = '<spot>'
asoc_prompt = '<asoc>'

type_start = '<0>'
type_end = '<1>'
text_start = '<2>'
span_start = '<5>'
null_span = '<6>'
null_label = '<7>'


class StructureMarker:
    def __init__(self) -> None:
        pass


class BaseStructureMarker(StructureMarker):
    def __init__(self) -> None:
        super().__init__()
        self.sent_start = '<0>'
        self.sent_end = '<1>'
        self.record_start = '<0>'
        self.record_end = '<1>'
        self.span_start = '<0>'
        self.span_end = '<1>'
        self.text_start = '<2>'
        self.source_span_start = '<3>'
        self.source_span_end = '<4>'
        self.target_span_start = '<5>'
        self.null_span = '<6>'
        self.null_label = '<7>'