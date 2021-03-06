__author__ = 'Raquel'

import xml.etree.ElementTree as ET
from urllib.request import urlopen
import urllib.parse
import re

# VIAF base urls
viaf_base_search = 'http://viaf.org/viaf/search'
viaf_base = 'http://viaf.org/viaf/'

# string for searching corporate names
corporate_names = 'local.corporateNames'

# String for searching all of viaf
all_viaf = 'all'

generic_terms = re.compile('-*(\s*(H|h)ome\s*|(W|w)elcome\s*|(T|t)he\s*|\s*(O|o)verview\s*|\s*(M|m)ain\s*|'
                           '\s*(P|p)age\s*)')


class Organization:
    def __init__(self, title):
        no_home_stuff = re.sub(generic_terms, '', title)
        self.name = re.sub('[^a-zA-Z0-9 -.]', '', no_home_stuff)
        self.string = '{}'.format(self.name)
    parentElem = None
    link = ''
    uri = None
    validated = False

    def validate_in_viaf(self):
        to_encode = self.string
        encoded_search_terms = pseudo_encode(to_encode)
        terms = [corporate_names, all_viaf, encoded_search_terms]
        query_string = 'query='
        for each in terms:
            query_string += each
            if each is not terms[len(terms)-1]:
                query_string += '+'
        data = {'recordSchema': 'BriefVIAF',
                'sortKeys': 'holdingscount'}
        values = urllib.parse.urlencode(data, 'utf-8')
        full_url = viaf_base_search + '?' + query_string + '&' + values
        self.link = full_url
        tree = ET.parse(urlopen(full_url))
        root = tree.getroot()
        records = root.find('{http://www.loc.gov/zing/srw/}records')
        if records is None:
            return False
        for child in records:
            record_data = child.find('{http://www.loc.gov/zing/srw/}recordData')
            cluster = record_data.find('{http://viaf.org/viaf/terms#}VIAFCluster')
            ctitle = cluster.find('{http://viaf.org/viaf/terms#}mainHeadings').\
                find('{http://viaf.org/viaf/terms#}data').find('{http://viaf.org/viaf/terms#}text')
            # Find a generic match
            search_term = re.compile('{}( \(.*\)$)*'.format(self.string), re.IGNORECASE)
            if re.search(search_term, str(ctitle.text)) is not None:
                viaf_id = cluster.find('{http://viaf.org/viaf/terms#}viafID')
                if viaf_id is not None:
                    self.uri = viaf_base + viaf_id.text + '/'
                    self.validated = True
        return self.validated

    def enhancement_info(self):
        status = '{} was not found in VIAF and therefore will not be part of any enhancements made to the doc'\
            .format(self.name)
        if self.validated:
            if self.uri:
                status = '{} was found in VIAF.'.format(self.name)
        return '{}\n {}\n {}\n {}\n'.format(self.name, self.validated, self.uri, status)

def pseudo_encode(string):
    string_to_encode = '"' + string + '"'
    return re.sub('\s', '%2B', string_to_encode)
