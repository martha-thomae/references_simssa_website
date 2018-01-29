"""Create markdown file by linking .bib and .html files."""

# !/usr/bin/python
# -*- coding: utf-8 -*-

import bibliography_parser as bp
from optparse import OptionParser
import bibtexparser
import Levenshtein
import time

if __name__ == "__main__":
    usage = "usage: html_references bib_references output_folder\n\n \
Example: python create_presentations.py ./presentations.html ./presentations.bib ./outputfolder/"
    opts = OptionParser(usage)
    (options, args) = opts.parse_args()
    html_references = args[0]
    bib_references = args[1]
    output_folder = args[2]

    html_span_elements = bp.html_iterator(html_references)
    bib_refs = bibtexparser.loads(open(bib_references).read()).entries

    for h_span in html_span_elements:
        # Obtain the title attribute in the <span> element
        # This attribute contains the metadata of the html reference
        html_attrib_title = h_span.get('title')
        # Retrieve the metadata:
        year_h = bp.year_extractor(html_attrib_title)
        author_h = bp.first_author_extractor(html_attrib_title)
        title_h = bp.title_extractor(html_attrib_title)

        # subsetting only same bib entries with same year
        candidates_by_year = [b for b in bib_refs if b['year'] == year_h]
        # authors are written differently in the bib entries and in the <span> elments of the html files (UTF-8)
        # and so the distance among strings is calculated and only the subset
        # of closest strings among candidates_by_year is kept
        similarities_by_author = [Levenshtein.ratio(author_h, candidate['author'].split(' and')[0]) for candidate in candidates_by_year]
        # The authors in the bib file are separated by an 'and'
        # So the first author is given by: candidate['author'].split(' and')[0]
        print(author_h + ", " + year_h + ", " + title_h[:10]) ##        



        m = max(similarities_by_author)  # returns all max indices
        candidates_by_author_idx = [i for i, j in enumerate(similarities_by_author) if j == m]
        candidates_by_author = [candidates_by_year[c] for c in candidates_by_author_idx]
        for candidate in candidates_by_author:  ##
            print(candidate['ID'])  ##

        # match now by closest title in the bib entries
        bib_titles = [bp.bracket_removal(c['title']) for c in candidates_by_author]
        similarities_by_titles = [Levenshtein.ratio(title_h, candidate['title']) for candidate in candidates_by_author]
        m = max(similarities_by_titles)
        candidates_by_titles_idx = [i for i, j in enumerate(similarities_by_titles) if j == m]
        candidates_by_titles = [candidates_by_author[c] for c in candidates_by_titles_idx]

        if len(candidates_by_titles) == 1:
            candidate_by_title = candidates_by_titles[0]
        else:
            h_ref = h_span.find_previous('div', {'class': 'csl-entry'})
            reftext = h_ref.text
            for candidate in candidates_by_titles:
                if candidate['address'] in reftext:
                    candidate_by_title = candidate

        work_title = candidate_by_title['title']
        work_title = bp.bracket_removal(work_title)
        #print(work_title)

        # Find the preceding element of the <span> element stored in h_span
        # It should be a <div class="cls-entry"> element
        # And its text ist he html reference
        h_ref = h_span.find_previous('div', {'class': 'csl-entry'})
        candidate_by_title['html_ref'] = h_ref.text
        selected_entry = bp.statamic_field_presentation_generator(candidate_by_title)
        today = (time.strftime("%Y-%m-%d"))
        bp.md_presentation_generator(selected_entry, work_title, output_folder, today + '-' + selected_entry['title'] + '.md')
        print()
        print(candidate_by_title['ID'])
        print("\n\n")
