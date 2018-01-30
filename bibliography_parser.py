import os
from bs4 import BeautifulSoup
import re

def html_iterator(html_file):
    """
    Returns a list of the <span> elements in the html file
    """
    ref_file = open(html_file)
    soup = BeautifulSoup(ref_file, 'html.parser')
    span_elements = soup.findAll('span')
    # The returned <span> elements contain the metadata for each reference of the html file
    return span_elements

def title_extractor(metadata_string):
    """
    Returns the title stored in <span>. The title, as well as other metadata for the reference, is part of 
    a large string which is stored in <span>'s attribute 'title' (here stored in the parameter metadata_string).
    The title returned is in UTF-8 format. 
    """

    # The title in the metadata_string is preceded by a substring of the form: 
    # 'rft.title', 'rft.atitle', or 'rft.btitle' (depending on the genre)
    # And it is followed by '&'
    genre = re.search('rft\.genre=([a-z]*)&', metadata_string)

    if genre == None:
        # For ALL Presentations, for ALL Media, and for SOME Publications (specifically, dissertations),
        # Zotero does not assign any 'genre'.
        # In ALL these cases, the title of the presentation/broadcast/publication follows the string "rft.title="
        title = re.search("rft\.title=([a-zA-Z0-9%()'.-]*)&rft", metadata_string).group(1)
        print("GENRE -> " + str(genre))
    else:
        genre_name = genre.group(1)
        print("GENRE -> " + genre.group(1))
        if genre_name == 'proceeding' or genre_name == 'bookitem' or genre_name == 'article':
            # For genres such as proceedings, bookitems, or journal articles,
            # the title of the publications follows the string "rft.atitle"
            title = re.search("rft\.atitle=([a-zA-Z0-9%()'.-]*)&rft", metadata_string).group(1)
        elif genre_name == 'book':
            # For the book genre, 
            # the title of the book follows the string "rft.btitle"
            title = re.search("rft\.btitle=([a-zA-Z0-9%()'.-]*)&rft", metadata_string).group(1)
        else:
            # Future possibilities?
            title = ""
            print ("EMPTY!")
            pass

    return title


def year_extractor(metadata_string):
    """
    Returns the year stored in <span>. The year, as well as other metadata for the reference, is part of 
    a large string which is stored in <span>'s attribute 'title' (here stored in the parameter metadata_string).
    """
    #The date of the reference is preceded by the substring 'rft.date=' and followed by '&'.

    # Assuming the year is the first thing that appears in the date (this might change in future versions?)
    years = re.findall('rft\.date=(.{4})', metadata_string)
    # If there are many years, pick the last one
    year = years[-1]
    return year


def first_author_extractor(metadata_string):
    """
    Returns the first author (UTF-8) in the form: last_name, first_name
    Example: Cumming, Julie E.
    """
    lastname = re.search("rft\.aulast=([a-zA-Z0-9%'.-]*)&", metadata_string).group(1)
    firstname = re.search("rft\.aufirst=([a-zA-Z0-9%'.()-]*)&rft", metadata_string).group(1)
    main_author = lastname + ', ' + firstname
    # The name of the author is retrieved in this format to facilitate the comparison with the first author in the bib file
    # (all authors in the bib file are stored in the form "last_name, first_name", even second and third authors)
    # Note: The variables 'lastname' and 'firstname' have only a single value, because only the first author has his/her
    # names separated into first and last (in the substrings following 'rft.aufirst' and 'rft.aulast', respectively).
    # The name of the other authors are shown in full (they follow the multiple 'rft.au' strings)
    return main_author

def bracket_removal(text_str):
    """
    Remove curly brackets from string
    """
    text_str = re.sub('{', '', text_str)
    text_str = re.sub('}', '', text_str)
    return text_str

def statamic_field_presentation_generator(bib_entry):
    """
    Return dictionary with information for presentation Statamic files from bib
    bibliographic entry and the Chicago 16th-formatted HTML file
    keys: ['slug', 'publish-date', 'presentation-place', 'presentation-year',
    'presented-by', 'citation']
    """
    if 'note' not in bib_entry:
        bib_entry['note'] = None
    return {'title': bib_entry['ID'],
            '_template': 'presentation',
            'conference': bib_entry['address'],
            'presentation_date': bib_entry['year'],
            'author': 'ehopkins',
            'upload': bib_entry['note'],
            'presented_by': bib_entry['author'],
            'publish_date': bib_entry['year'],
            'citation': bib_entry['html_ref']}


def statamic_field_publication_generator(bib_entry):
    """
    Return dictionary with information for publication Statamic files from bib
    bibliographic entry and the Chicago 16th-formatted HTML file

    """
    # for handling non incollection ('booktitle') types
    if bib_entry['ENTRYTYPE'] == 'article':
        bib_entry['booktitle'] = bib_entry['journal']
    elif bib_entry['ENTRYTYPE'] == 'phdthesis':
        bib_entry['booktitle'] = bib_entry['ENTRYTYPE']
    elif bib_entry['ENTRYTYPE'] == 'book':
        bib_entry['booktitle'] = bib_entry['ENTRYTYPE']
    if 'note' not in bib_entry:
        bib_entry['note'] = None
    return {'title': bib_entry['ID'],
            '_template': 'publication',
            'conference': bib_entry['booktitle'],
            'first_author': bib_entry['author'],
            'year': bib_entry['year'],
            'author': 'ehopkins',
            'upload': bib_entry['note'],
            'citation': bib_entry['html_ref']}


def statamic_field_media_generator(bib_entry):
    """
    Return dictionary with information for media Statamic files from bib
    bibliographic entry and the Chicago 16th-formatted HTML file
    keys: ['slug', 'publish-date', 'presentation-place', 'presentation-year',
    'presented-by', 'citation']
    """
    if 'note' not in bib_entry:
        bib_entry['note'] = None
    return {'title': bib_entry['ID'],
            '_template': 'media',
            'conference': bib_entry['address'],
            'presentation_date': bib_entry['year'],
            'author': 'ehopkins',
            'upload': bib_entry['note'],
            'presented_by': bib_entry['author'],
            'publish_date': bib_entry['year'],
            'citation': bib_entry['html_ref']}

def url_link_encoder(citation_str, upload_url, title):
    """
    Insert HTML code in the citation string
    """
    # Make the title of the citation_str link to the upload_url

    # The title extracted from the metadata of each entry in the html file
    # (this is, the string in the span element that follows 'rft.title=')
    # corresponds to the title entered in Zotero (with the exact same capitalization).
    
    # The title of the citation_str (the text of each reference in the html) 
    # has a capitalization that corresponds to a given citation style (e.g., Chicago 17)
    
    # To find the title in the citation_str, we need both of them to be written using the same capitalization.

    # Lower case version of both the citation_str and the title
    reference_low = citation_str.lower()
    title_low = title.lower()

    # Determine the indices where the title is found in the citation_str
    title_start = reference_low.find(title_low)
    title_end = title_start + len(title_low)

    # Find the title in the citation_str
    ref_title = citation_str[title_start:title_end]

    # Substitute the title by a linked version of itself, which links to the upload_url
    url_string = ''.join(['<a href="', upload_url, '">', ref_title, '</a>'])
    print(title in citation_str)
    citation_str = citation_str.replace(ref_title, url_string)
    return citation_str


def md_presentation_generator(bib_dict, presentation_title, output_folder, outfile):
    """
    Receive a dictionary with SIMSSA presentations, and returns markdown
    file properly formatted for SIMSSA presentations
    """
    # print bib_dict
    md = '---\n\
title: {0}\n\
_template: {1}\n\
conference: {2}\n\
presentation_date: "{3}"\n\
author: {4}\n\
upload: {5}\n\
presentation_author: {6}\n\
presentation_year: "{7}"\n\
---\n'.format(
    bib_dict['title'],
    bib_dict['_template'],
    bib_dict['conference'],
    bib_dict['presentation_date'],
    bib_dict['author'],
    bib_dict['upload'],
    bib_dict['presented_by'],
    bib_dict['publish_date'])
    with open(os.path.join(output_folder, outfile), 'w') as out_f:
        out_f.write(md)
        if bib_dict['upload'] is not None:
            citation_str = url_link_encoder(
                bib_dict['citation'],
                bib_dict['upload'],
                presentation_title)
        else:
            citation_str = bib_dict['citation']
        out_f.write(citation_str)


def md_publication_generator(bib_dict, publication_title, output_folder, outfile):
    """
    Receive a dictionary with SIMSSA publications, and returns markdown
    file properly formatted for SIMSSA publications
    """
    #print(bib_dict)
    md = '---\n\
title: {0}\n\
_template: {1}\n\
conference: {2}\n\
year: "{3}"\n\
first_author: {4}\n\
upload: {5}\n\
---\n'.format(
    bib_dict['title'],
    bib_dict['_template'],
    bib_dict['conference'],
    bib_dict['year'],
    bib_dict['first_author'],
    bib_dict['upload'])
    #print('1')
    with open(os.path.join(output_folder, outfile), 'w') as out_f:
        out_f.write(md)
        if bib_dict['upload'] is not None:
            citation_str = url_link_encoder(
                bib_dict['citation'],
                bib_dict['upload'],
                publication_title)
        else:
            citation_str = bib_dict['citation']
        
        #out_f.write(citation_str.encode('utf-8')) #REPLACED THIS ONE#
        out_f.write(citation_str)


def md_media_generator(bib_dict, broadcast_title, output_folder, outfile):
    """
    Receive a dictionary with SIMSSA presentations, and returns markdown
    file properly formatted for SIMSSA presentations
    """
    # print bib_dict
    md = '---\n\
title: {0}\n\
_template: {1}\n\
conference: {2}\n\
presentation_date: "{3}"\n\
author: {4}\n\
upload: {5}\n\
presentation_author: {6}\n\
presentation_year: "{7}"\n\
---\n'.format(
    bib_dict['title'],
    bib_dict['_template'],
    bib_dict['conference'],
    bib_dict['presentation_date'],
    bib_dict['author'],
    bib_dict['upload'],
    bib_dict['presented_by'],
    bib_dict['publish_date'])
    with open(os.path.join(output_folder, outfile), 'w') as out_f:
        out_f.write(md)
        if bib_dict['upload'] is not None:
            citation_str = url_link_encoder(
                bib_dict['citation'],
                bib_dict['upload'],
                broadcast_title)
        else:
            citation_str = bib_dict['citation']
        out_f.write(citation_str)
