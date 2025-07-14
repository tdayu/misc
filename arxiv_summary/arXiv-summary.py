import re, requests, time, json, yaml
from datetime import date, timedelta
from optparse import OptionParser
from pylatex import Document, Section, Subsection, Command, NoEscape
from pylatex import Tabular, MultiColumn, NoEscape
import xml.etree.ElementTree as ET

def parse_args():
    parser = OptionParser(usage="usage: %prog [options] arg")
    parser.add_option(
        "-s",
        "--start",
        dest="start",
        help="Start date in format YYYY-MM-DD",
        metavar="<Start date>",
        default=(date.today() - timedelta(days=7)).isoformat()
    )
    parser.add_option(
        "-e",
        "--end",
        dest="end",
        help="End date in format YYYY-MM-DD",
        metavar="<End date>",
        default=date.today().isoformat()
    )
    parser.add_option(
        "-y",
        "--yaml",
        dest="yaml",
        help="Input option YAML file.",
        metavar="<YAML Option>",
    )
    parser.add_option(
        "-j",
        "--json",
        dest="json",
        help="Output JSON file.",
        metavar="<JSON Output>",
    )
    parser.add_option(
        "-l",
        "--latex",
        dest="latex",
        help="Output latex file.",
        metavar="<Latex Output>",
    )
    (options, args) = parser.parse_args()
    return options, args


def process_date(start, end, date_query):
    pattern = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
    start_match = pattern.match(start)
    end_match = pattern.match(end)
    if not start_match:
        raise ValueError(f"Invalid date format: {start}. Expected YYYY-MM-DD.")
    if not end_match:
        raise ValueError(f"Invalid date format: {end}. Expected YYYY-MM-DD.")

    starttime = f"{start_match.group(1)}{start_match.group(2)}{start_match.group(3)}0000"
    endtime = f"{end_match.group(1)}{end_match.group(2)}{end_match.group(3)}2359"

    return f"{date_query}:[{starttime}+TO+{endtime}]"


class Node:
    def __init__(self, value):
        self.value = value

    def query_string(self, prefix=None, group=False):
        query = f"{prefix}:{self.value}" if prefix else self.value
        if group:
            query = f"%28{query}%29"
        return query

class OrNode:
    def __init__(self, children):
        self.children = children

    def query_string(self, prefix=None, group=False):
        query = "+OR+".join([f"{prefix}:{child}" if prefix else child for child in self.children])
        if group:
            query = f"%28{query}%29"
        return query

class AndNode:
    def __init__(self, children):
        self.children = children

    def query_string(self, prefix=None, group=False):
        query = "+AND+".join([f"{prefix}:{child}" if prefix else child for child in self.children])
        if group:
            query = f"%28{query}%29"
        return query

class AndNotNode:
    def __init__(self, childA, childB):
        self.childA = childA
        self.childB = childB

    def query_string(self, prefix=None, group=False):
        query = f"{prefix}:{self.childA}+ANDNOT+{prefix}:{self.childB}" if prefix else f"{self.childA}+ANDNOT+{self.childB}"
        if group:
            query = f"%28{query}%29"
        return query


def format_whitespace(text):
    leading_whitespace = re.compile(r"^\s+")
    newline = re.compile(r"\n\s*")
    formatted = leading_whitespace.sub("", text)
    formatted = newline.sub(" ", formatted)
    return formatted


def format_date(date_str):
    date_str = time.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    date_str = time.strftime("%Y %B %d", date_str)
    return date_str


class ArXivEntry:
    def __init__(self, title, authors, abstract, submitted, updated, arxivID, link, categories):
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.submitted = submitted
        self.updated = updated
        self.arxivID = arxivID
        self.link = link
        self.categories = categories

    def __str__(self):
        string = [
            f"Title: {self.title}",
            f"Authors: {', '.join(self.authors)}",
            f"Abstract: {self.abstract}",
            f"Submitted Date: {self.submitted}",
            f"Updated Date: {self.updated}",
            f"ArXiv Identifier: {self.arxivID}",
            f"Link: {self.link}",
            f"Categories: {', '.join(self.categories)}",
        ]
        return "\n".join(string)


class ArXivEntryEncoder(json.JSONEncoder):
    def default(self, object):
        if isinstance(object, ArXivEntry):
            return {
                "title": object.title,
                "authors": object.authors,
                "abstract": object.abstract,
                "submitted": object.submitted,
                "updated": object.updated,
                "arxivID": object.arxivID,
                "link": object.link,
                "categories": object.categories,
            }
        return super().default(object)


def format_link(link):
    pattern = re.compile(r"https?://arxiv.org/abs/([0-9]{4}\.[0-9]{4})")
    match = pattern.match(link)
    if not match:
        raise ValueError(f"Invalid link format: {link}. Expected arxiv.org/abs/YYYY.NNNN.")
    arxivID = match.group(1)
    link = match.group(0)

    return arxivID, link


def parse_entry(entry):
    title = entry.find("{http://www.w3.org/2005/Atom}title").text
    title = format_whitespace(title)

    authors = entry.findall("{http://www.w3.org/2005/Atom}author")
    authors = [author.find("{http://www.w3.org/2005/Atom}name").text for author in authors]
    authors = [format_whitespace(author) for author in authors]

    abstract = entry.find("{http://www.w3.org/2005/Atom}summary").text
    abstract = format_whitespace(abstract)

    submitted = entry.find("{http://www.w3.org/2005/Atom}published").text
    submitted = format_date(submitted)

    updated = entry.find("{http://www.w3.org/2005/Atom}updated").text
    updated = format_date(updated)

    link = entry.find("{http://www.w3.org/2005/Atom}id").text
    arxivID, link = format_link(link)

    categories = entry.findall("{http://www.w3.org/2005/Atom}category")
    categories = [category.get("term") for category in categories]

    entry = ArXivEntry(
        title=title,
        authors=authors,
        abstract=abstract,
        submitted=submitted,
        updated=updated,
        arxivID=arxivID,
        link=link,
        categories=categories,
    )
    return entry

def query_arxiv(yaml_file, start_date, end_date):
    with open(yaml_file, "r") as file:
        query_options = yaml.safe_load(file)

    # Create the queries
    title_queries = [
        Node(query).query_string("ti") for query in query_options["queries"]
    ]
    abstract_queries = [
        Node(query).query_string("abs") for query in query_options["queries"]
    ]

    title_vetoes = [
        Node(veto).query_string("ti") for veto in query_options["vetoes"]
    ]
    abstract_vetoes = [
        Node(veto).query_string("abs") for veto in query_options["vetoes"]
    ]

    categories = [
        Node(category).query_string("cat") for category in query_options["categories"]
    ]
    categories = OrNode(categories).query_string(group=True)

    queries = title_queries
    queries = OrNode(queries).query_string(group=True)
    vetoes = title_vetoes + abstract_vetoes
    vetoes = OrNode(vetoes).query_string(group=True)
    query = AndNotNode(queries, vetoes).query_string(group=True)

    # Get the arXiv entries submitted and last updated in this time period
    entries = dict()
    for date_type in ["submitted", "lastUpdated"]:
        date_filter = process_date(start_date, end_date, f"{date_type}Date")
        # search_query = f"search_query={query}+AND+{categories}"
        search_query = f"search_query={query}+AND+{categories}+AND+{date_filter}"
        max_results = "max_results=50"
        sort = f"sortBy={date_type}Date&sortOrder=descending"
        full_query = "&".join([search_query, max_results, sort])
        url = f"https://export.arxiv.org/api/query?{full_query}"

        response = requests.get(url)
        if not response.status_code == 200:
            raise Exception(f"Failed to fetch data from arXiv: {response.status_code}")
        root = ET.fromstring(response.content)
        queried_entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        queried_entries = [parse_entry(entry) for entry in queried_entries]
        entries[date_type] = queried_entries

    # Remove updated entries from submitted entries
    submitted_arXivIDs = [ entry.arxivID for entry in entries["submitted"] ]
    entries["lastUpdated"] = [
        entry for entry in entries["lastUpdated"]
        if entry.arxivID not in submitted_arXivIDs
    ]

    return entries

def convert_to_latex(latex_path, entries, start_date, end_date):
    start_date = date.fromisoformat(start_date)
    end_date = date.fromisoformat(end_date)
    start_date = start_date.strftime("%y/%m/%d")
    end_date = end_date.strftime("%y/%m/%d")

    title = [
        r"B-Hadrons and Quarkonia ArXiv Summary\vspace{0.5cm}\\",
        "\n\large ",
        f"From {start_date} to {end_date}",
        # r"\vspace{0.1cm}\\",
        # f""
    ]
    title = "".join(title)

    doc = Document()
    doc.packages.append(NoEscape(r'\usepackage{hyperref}'))
    doc.packages.append(NoEscape(r'\usepackage{xcolor}'))
    doc.packages.append(NoEscape(r'\usepackage[margin=1.5in]{geometry}'))
    # Define a custom LaTeX command for hyperlinks
    doc.preamble.append(NoEscape(r'\newcommand{\hlink}[2]{\href{#1}{\textcolor{blue}{#2}}}'))
    doc.preamble.append(Command('title', NoEscape(title)))
    doc.preamble.append(Command('date', ''))
    doc.append(NoEscape(r'\maketitle'))
    doc.append(NoEscape(r'\tableofcontents'))
    doc.append(NoEscape(r'\newpage'))

    for key, label in zip(["submitted", "lastUpdated"], ["Newly Submitted", "Recently Updated"]):
        with doc.create(Section(f"{label} Papers")):
            for entry in entries.get(key, []):
                with doc.create(Subsection(NoEscape(entry.title))):
                    with doc.create(Tabular('p{0.12\linewidth}p{0.86\linewidth}', row_height=1.2)) as table:
                        table.add_row((NoEscape(r'\textbf{Authors}:'), NoEscape(", ".join(entry.authors))))
                        table.add_row((NoEscape(r'\textbf{arXivID}:'), NoEscape(r'\hlink{' + entry.link + '}{' + entry.arxivID + '}')))
                        if key == "lastUpdated":
                            table.add_row((NoEscape(r'\textbf{Updated}:'), NoEscape(entry.updated)))
                        table.add_row((NoEscape(r'\textbf{Submitted}:'), NoEscape(entry.submitted)))
                        table.add_row((NoEscape(r'\textbf{Categories}:'), NoEscape(", ".join([f"\\texttt{{{category}}}" for category in entry.categories]))))
                    doc.append(NoEscape('\n\n'))
                    doc.append(NoEscape(r'\vspace{0.3cm}'))
                    doc.append(NoEscape(r'\noindent\textbf{\underline{Abstract:}}'))
                    doc.append(NoEscape(r'\vspace{0.1cm}\\'))
                    doc.append(NoEscape(f"\hspace{{2em}}{entry.abstract}\n\n"))

        # self.title = title
        # self.authors = authors
        # self.abstract = abstract
        # self.submitted = submitted
        # self.updated = updated
        # self.arxivID = arxivID
        # self.link = link
        # self.categories = categories

    doc.generate_tex(latex_path)

    # if hasattr(entries, 'latex') and entries.latex:
    #     doc.generate_pdf(entries.latex, clean_tex=False)

if __name__ == "__main__":
    options, args = parse_args()

    entries = query_arxiv(
        yaml_file=options.yaml,
        start_date=options.start,
        end_date=options.end
    )

    if options.json:
        with open(options.json, "w") as file:
            json.dump(entries, file, cls=ArXivEntryEncoder, indent=2)

    convert_to_latex(latex_path=options.latex, entries=entries, start_date=options.start, end_date=options.end)
