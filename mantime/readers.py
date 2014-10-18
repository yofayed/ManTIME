#!/usr/bin/env python
#
#   Copyright 2014 Michele Filannino
#
#   gnTEAM, School of Computer Science, University of Manchester.
#   All rights reserved. This program and the accompanying materials
#   are made available under the terms of the GNU General Public License.
#
#   author: Michele Filannino
#   email:  filannim@cs.man.ac.uk
#
#   For details, see www.cs.man.ac.uk/~filannim/

"""It contains all the readers for ManTIME.

   A reader must have a parse() method which is responsible for reading the
   input file and return a Document object, which is our internal
   representation of any input document (whetever the format is).

   In order to force the existence of the parse() method I preferred Python
   interfaces to the duck typing practice.
"""

from abc import ABCMeta, abstractmethod
import xml.etree.cElementTree as etree
from StringIO import StringIO

from corenlp import StanfordCoreNLP

from model import Document
from settings import PATH_CORENLP_FOLDER

CORENLP = StanfordCoreNLP(PATH_CORENLP_FOLDER)


class Reader(object):
    """This class is an abstract reader for ManTIME."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def parse(self, text):
        pass


class FileReader(Reader):
    """This classs is an abstract file reader for ManTIME."""
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def parse(self, file_path):
        pass


class TempEval3FileReader(FileReader):
    """This class is a reader for TempEval-3 files."""

    def __init__(self, annotation_format='IO'):
        super(TempEval3FileReader, self).__init__()
        self.tags_to_spot = {'TIMEX3', 'EVENT', 'SIGNAL'}
        self.annotations = []
        self.annotation_format = annotation_format

    def parse(self, file_path):
        """It parses the content of file_path and extracts relevant information
        from a TempEval-3 annotated file. Those information are packed in a
        Document object, which is our internal representation.
        """
        xml_document = etree.parse(file_path)
        document = Document(file_path)

        text_node = xml_document.findall(".//TEXT")[0]
        text = etree.tostring(text_node, method='text')
        xml = etree.tostring(text_node)
        xpath_dct = ".//TIMEX3[@functionInDocument='CREATION_TIME']"
        # StanfordParser strips internally the text :(
        l_strip_chars = len(text.lstrip()) - len(text)

        document.dct = xml_document.findall(xpath_dct)[0].attrib['value']
        document.text = text
        document.annotations = self.__get_annotations(xml, l_strip_chars)
        document.stanford_tree = CORENLP.raw_parse(document.text)
        document.push_classes(self.annotation_format)
        return document

    def __get_annotations(self, source, start_offset=0):
        '''It returns the annotations found in the document in the following
           format:
           [
            ('TAG', {ATTRIBUTES}, (start_offset, end_offset)),
            ('TAG', {ATTRIBUTES}, (start_offset, end_offset)),
            ...
            ('TAG', {ATTRIBUTES}, (start_offset, end_offset))
           ]
        '''
        annotations = []
        for event, element in etree.iterparse(
                StringIO(source), events=('start', 'end')):
            if event == 'start':
                if element.tag in self.tags_to_spot:
                    end_offset = start_offset + len(element.text)
                    annotations.append((element.tag, element.attrib,
                                        (start_offset, end_offset)))
                start_offset += len(element.text)
            elif event == 'end':
                if element.text is not None and element.tail is not None:
                    start_offset += len(element.tail)
        return annotations


Reader.register(FileReader)
FileReader.register(TempEval3FileReader)


def main():
    '''Simple ugly non-elegant test.'''
    import sys
    import pprint
    file_reader = TempEval3FileReader(annotation_format='IO')
    document = file_reader.parse(sys.argv[1])
    pprint.pprint(document.__dict__)

if __name__ == '__main__':
    main()