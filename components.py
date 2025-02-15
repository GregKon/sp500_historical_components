"""
Use MediaWiki Revisions API to get historical index components according to the 
revision at a particular date.

MediaWiki Revisions API: https://www.mediawiki.org/wiki/API:Revisions
Wikipedia List of S&P500 Companies: https://en.wikipedia.org/wiki/List_of_S%26P_500_companies 

Comments:
    Do not get confused between market indices (S&P500, Russell 1000) and pandas DataFrame indices
"""
import pandas as pd
import requests
import urllib.parse
import datetime
from typing import List, Dict
from utils import isoformat
import os

wikipedia_pages = {
    'SPX': 'List of S&P 500 companies',
    'NASDAQ': "Nasdaq-100#Components",
    'Nasdaq100' : "Nasdaq-100",
    'S400' : 'List of S&P 400 companies',
    'DowJones': 'Dow_Jones_Industrial_Average',
    'Russell_1000' :'Russell_1000_Index',
    'FTSE_350' : 'FTSE_350_Index',
    'Forbes2000': 'Forbes_Global_2000',
    
}
wikipedia_api_url = "https://en.wikipedia.org/w/api.php"
wikipedia_page_url_base = "https://en.wikipedia.org/w/index.php"

def get_revisions_metadata(page_title: str, rvstart=None, rvend=None, rvdir: str = 'newer', rvlimit: int = 1, S=requests.Session(), **kwargs) -> List[Dict]:
    """Get metadata for revision(s) using MediaWiki API

    Args:
        page: page title
        rvstart: get revisions starting from this date. Most common date formats are accepted. Default = None (no limit on rvstart)
        rvend: get revisions until this date. Most common date formats are accepted. Default = None (no limit on rvend)
        rvdir: direction of revision dates for results. 
            If 'newer', results are ordered old->new (rvstart < rvend). Convenient for getting the first revision after a given date.
            If 'older', results are ordered new->old (rvstart > rvend). Convenient for getting the latest revision before a given date.
            Default = 'newer' 
        S: HTTP session to use. Default = requests.Session()
        kwargs: additional params to pass to the MediaWiki API query. See https://www.mediawiki.org/wiki/API:Revisions

    Returns:
        Revision(s) metadata
    """
    query_params = {
        "action": "query",
        "prop": "revisions",
        "titles": page_title,
        "rvprop": "ids|timestamp|user|comment",
        "rvslots": "main",
        "formatversion": "2",
        "format": "json",
        "rvlimit": rvlimit,
        "rvdir": rvdir,
    }
    # cleanup dates
    if rvstart is not None:
        query_params['rvstart'] = isoformat(rvstart)
    if rvend is not None:
        query_params['rvend'] = isoformat(rvend)
    # optional query_params
    for k, v in kwargs.items():
        query_params[k] = v
    print('query_params')
    print(query_params)
    r = S.get(url=wikipedia_api_url, params=query_params)
    data = r.json()
    print('response:', data, flush=True)
    pages = data["query"]["pages"]
    revisions = pages[0]['revisions']
    print('revision')
    print(revisions)
    return revisions

def get_index_components_at(index: str = 'SPX', when: str = None) -> pd.DataFrame:
    """Returns index components at a given date, according to the latest update on Wikipedia before that date.

    Args:
        index: The index to get components for. Currently only 'SPX' is supported. Default = 'SPX'
        when: The date when to search components. Default = today

    Returns:
        
    """
    if when is None:
        when = datetime.datetime.today()
    page = wikipedia_pages[index]
    revisions = get_revisions_metadata(page, rvdir='older', rvstart=when) # get latest revision before 'when'
    revision = revisions[0]
    print(f"Got results from {revision['timestamp']}")
    table = pd.read_html(f"{wikipedia_page_url_base}?title={urllib.parse.quote(page)}&oldid={revision['revid']}")
    #components_df = table[0]
    for df in table: # usually the components df will be table[0], but sometimes there is a table before that just holds comments about the article, which we ignore.
        if 'Symbol' in df.columns:
            df = df.set_index('Symbol')
            break
        elif 'Ticker symbol' in df.columns:
            df = df.set_index('Ticker symbol')
            break
    df.index.name = 'Symbol'
    return df.sort_index()

def get_index_components_history(index: str = 'SPX', start_date=None, end_date=None, freq='M'):
    """Get the historical components between start_date and end_date at a given frequency (e.g. monthly)

    Args:
        index: The index to get components for. Default = 'SPX'
        start_date:
        end_date:
        freq: pandas frequency string (https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases)

    Returns:
    """
    if end_date is None:
        end_date = datetime.date.today()
    dates = pd.date_range(start=start_date, end=end_date, freq=freq)
    historical_components = {}
    for date in dates:
        components_at_date = get_index_components_at(index=index, when=date)
        historical_components[str(date)] = list(components_at_date.index)
    return historical_components

def components_to_separate_csv(components: dict, index: str) -> None:
    '''
    For every row create separate file with the list of components coma separated, in name is date of component
    '''
    for date, components_list in components.items():
        # Sprawdź, czy wszystkie elementy w components_list są stringami
        if all(isinstance(component, str) for component in components_list):
            # Format date to remove time and replace invalid characters
            formatted_date = date.split()[0]  # Remove time part
            with open(f"{index}/{index}_{formatted_date}.csv", 'w') as f:
                f.write(','.join(components_list))
        else:
            print(f"Skipping date {date} due to non-string components")

if __name__ == '__main__':
    
    freq = 'QS'        
    for index in wikipedia_pages.keys():
        print('Get current components for', index) 
        #create directory named index
        os.makedirs(index, exist_ok=True)
        
        #df = get_index_components_at(index=index)
        #print(df.index, flush=True)
        #print('Get historical components at October 2018')
        #sp500_2015 = get_index_components_at(index=index, when='2020-01-01')
        #print(sp500_2015.index, flush=True)
        
        print('Get historical components monthly since 2008') # before then, the list was not in table format
        components_dict = get_index_components_history(index=index, start_date='2015-01-01', freq=freq)        
        components_to_separate_csv(components_dict, index)
        # components_dict = pd.DataFrame.from_dict(components_dict, orient='index')
        # components_dict.to_csv(index + '/' + index + '_components_' + freq + '.csv')


