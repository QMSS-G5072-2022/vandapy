#!/usr/bin/env python
# coding: utf-8

# In[1]:


#import packages
import numpy as np
import requests
import pandas as pd 
import re
import mock
import pytest


# In[20]:


def search(q = "", page_size = 10, page = 1):
    """
    Searches the Victoria & Albert Musuem (V&A) API for items in their online collection.
    
    Users can specify what they are looking for by adjusting their input to either 1,2,3,4 or 5.
    
    1 - searches for items matching the query in the V&A API in general
    2 - searches only for types of objects which match the query
    3 - searches only for certain materials or techniques which match the query
    4 - searches only for certain a certain person, persons, or an organisation which match the query
    5 - searches only for certain titles of objects which match the query
    
    The V&A API does not return certain attributes of objects such as what they are made of or what technique was used
    intuitively. For example, to properly search for all items made through a tehcnique like "etching" one needs to know the serial code for etching. 
    With this function, one can instead search the API using specific paramters, allowing you to do a constrained query depending on what you are looking for.

    This function returns the resulting search results in a pandas dataframe with useful information as columns.

    Parameters
    ----------
    page : int
        url paramter for which page is returned. The first page is returned by default.
    page_size : int
        url parameter for number of rows to return per page. A higher "per_page" will return more results up to a maximum of 100.
    q : obj
        search query for specific items matching query. 

    Returns
    -------
    objects_df: pd.dataframe
        The resulting pandas dataframe from the search which includes details on the items in question. 

    Examples
    --------
    >>> search("China")
        What kind of search were you looking to do?
        Type 1 to search generally
        Type 2 to search for a certain type of object (i.e book, painting)
        Type 3 to search for a certain material or technique (i.e silver as a material or etching as a technique)
        Type 4 to search for certain people, a person, or an organisation
        Type 5 to search for a certain title of the object (i.e the name of a painting)1
        Success!
        There are 25450 objects associated with the query China
        Type                  Title    Construction Date    Primary Location  systemNumber _primaryImageID      Maker                Association
        Cup and saucer        Tulip        1931                Longton            O163544     2010EH1952    Paragon China Limited     maker
        Coffee pot and cover  Tulip        1931                Longton            O163543     2010EH1942    Paragon China Limited     maker
            """
    assert type(q) == str, "The query must be in string form"
    acceptables = ["1","one","2","two","3","three","4","four","5","five"] #set accepted answers
    
    x = input("What kind of search were you looking to do?\n" #ask user for the kind of search they want to do
    "Type 1 to search generally\n"
    "Type 2 to search for a certain type of object (i.e book, painting)\n"
    "Type 3 to search for a certain material or technique (i.e silver as a material or etching as a technique)\n"
    "Type 4 to search for certain people, a person, or an organisation\n"
    "Type 5 to search for a certain title of the object (i.e the name of a painting)")

    if x not in acceptables:
        raise Exception("Input is invalid. Function only accepts 1,2,3,4 and 5") #raise error if type of search is not legitimate

    if x == "1" or x.lower() == "one": #adjust search paramter to what the user requested
        params = {'q':q, "page_size":page_size, "page": page}
    if x == "2" or x.lower() == "two":
        params = {'q_object_type':q, "page_size":page_size, "page": page}
    if x == "3" or x.lower() == "three":
        params = {'q_material_technique':q, "page_size":page_size, "page": page}
    if x == "4" or x.lower() == "four":
        params = {'q_actor':q}
    if x =="5" or x.lower() == "five":
        params = {'q_object_title':q, "page_size":page_size, "page": page}
        
    url = 'https://api.vam.ac.uk/v2/objects/search?' #set url
    try:
        response = requests.get(url, params = params)
        response.raise_for_status()
    except HTTPError as http_err: 
        print(f'HTTP error occurred: {http_err}') #raise error for HTTP
    except Exception as err: 
        print(f'Other error occurred: {err}') #raise any other error
    else:
        print('Success!') #print if no errors
        
    object_data = response.json() #get json info
    object_info = object_data["info"] #get info for objects returned
    record_count = object_info["record_count"] #get how many objects were returned
    page_count = object_info["pages"]
    if record_count == 0:
        print("No results!") #return message when there were no results
    else:
        object_records = object_data["records"] #get records of all objects returned
        objects_df = pd.DataFrame(object_records) #turn objects into pandas dataframe
        objects_df = objects_df[['objectType', '_primaryTitle','_primaryDate','_primaryMaker','_primaryPlace','systemNumber','_primaryImageId']] #select for only relevant columns
        objects_df = pd.concat([objects_df.drop(['_primaryMaker'], axis=1), objects_df['_primaryMaker'].apply(lambda x: pd.Series(x,dtype = "object"))], axis=1) #_primaryMaker column contains both the artist and association so we seperate them
        objects_df = objects_df.rename(columns={'objectType': 'Type', '_primaryTitle': 'Title','_primaryDate':'Construction Date','name':'Maker','association':'Association','_primaryPlace':'Primary Location'}) #rename columns
        print(f"There are {record_count} objects associated with the query {q} and {page_count} different pages")

        return (objects_df) #return dataframe


# In[3]:


def page_summary(q = ""):
    """
    Returns summary statistics for a specific search page in the Victoria & Albert Musuem (V&A) API in a python dictionary.

    Parameters
    ----------
    q : obj
        search query for specific items matching query. 

    Returns
    -------
    dicitonary: dict
        All calculated summary statistics presented in dictionary form. 

    Examples
    --------
    >>> search("Da Vinci")
        What kind of search were you looking to do?
        Type 1 to search generally
        Type 2 to search for a certain type of object (i.e book, painting)
        Type 3 to search for a certain material or technique (i.e silver as a material or etching as a technique)
        Type 4 to search for certain people, a person, or an organisation
        Type 5 to search for a certain title of the object (i.e the name of a painting)4
        Success!
        There are 1046 objects associated with the query Da Vinci
        Search is associated with these many results: 15
        Search is assocaited with these many unique makers: 6
        Location most associated with search: Italy
        Search contains works created in these centuries: []
        Search contains these types of works: ['Oil painting' 'manuscript' 'Bas-relief' 'Drawing' 'Group'
         'Statuette - group' 'Statuette ' 'Printing plate' 'Statuette' 'Print']
    """
    
    objects_df = search(q)
    
    if objects_df is None:
        print("No summary statistics can be computed as there were no results!")
        
    else:
    
        ##summary statistics

        #number of works associated with search
        num_works = len(objects_df["Title"])
        print("Search is associated with these many results:",len(objects_df["Title"]))

        #number of artists associated with search
        num_artists = len(objects_df["Maker"].unique())
        print("Search is assocaited with these many unique makers:", len(objects_df["Maker"].unique()))

        #most popular location
        pop_loc = objects_df.mode()['Primary Location'][0]
        print("Location most associated with search:",objects_df.mode()['Primary Location'][0])

       #centuries included in search
        out = [re.sub(r'\D', '', year) for year in objects_df["Construction Date"] if len(year) <5] #get only digits below five
        out = [i for i in out if i] #only include matches without missing values
        century = set([1+(int(i)-1)//100 for i in out]) #get century for item
        century = list(century) #get unique centuries and put into list
        print("Search contains works created in these centuries:",century)

        #types of works in search
        types = objects_df['Type'].unique()
        print("Search contains these types of works:",objects_df['Type'].unique())
        
        #dictionary of values
        dictionary = {'num_works':num_works,'num_artistis':num_artists,'pop_loc':pop_loc,"centuries":century,"types":types}
        return(dictionary)


# In[18]:


def get_images(q = "", region = "full", size = "full", rotation = "0", quality = "default", p_form = "jpg", page = 1, page_size = 100):
    """
    This function allows a user to get images associated with their query where availible. Users can also
    customise the dimensions of the images and it's quality by adjusting certain parameters.
    
    Returns a print statement with links to the image obtained and a list of all urls of the images.

    Parameters
    ----------
    q : obj
        Search query for specific items matching query
    region: obj
        Specify the area of the image
    size: obj
        Specify the size of the image returned
    rotation: obj
        Specify the degrees the image is rotated by (0,90,180,270,360)
    quality: obj
        Specify the quality of image (default, grey, bitonal)
    format: obj
        Currently only JPEG format is supported
    page: int
        Specify which page from search we want images from. Default is first page.
    page_size: int
        Specify how many items can be listed per page. Up to a maximum of 100.

    Returns
    -------
    url_list: list
        All links presented in list format.

    Examples
    --------
    >>> get_images("Barbie")
    What kind of search were you looking to do?
    Type 1 to search generally
    Type 2 to search for a certain type of object (i.e book, painting)
    Type 3 to search for a certain material or technique (i.e silver as a material or etching as a technique)
    Type 4 to search for certain people, a person, or an organisation
    Type 5 to search for a certain title of the object (i.e the name of a painting)1
    Success!
    There are 84 objects associated with the query Barbie and 9 different pages
    https://framemark.vam.ac.uk/collections/2006AE7822/full/full/0/default.jpg
    https://framemark.vam.ac.uk/collections/2006AN0713/full/full/0/default.jpg
    https://framemark.vam.ac.uk/collections/2014GX5584/full/full/0/default.jpg
    https://framemark.vam.ac.buk/collections/2016HY8414/full/full/0/default.jpg
    https://framemark.vam.ac.uk/collections/2006BF0421/full/full/0/default.jpg
        
    """
    object_df = search(q , page = page, page_size = page_size)
    imageids = []
    try:
        [imageids.append(i) for i in object_df["_primaryImageId"]]
        imageids = list(filter(lambda item: item is not None, imageids))
        url_list = []
        for i in imageids:
            url = f"https://framemark.vam.ac.uk/collections/{i}/{region}/{size}/{rotation}/{quality}.{p_form}"
            url_list.append(url)
            print(url)
            
    except:
        ("Something went wrong. Most likely there are no image ids associated with your query")
    return (url_list)


# In[5]:


def cluster_summary(q = ""):
    """
    Returns cluster summaries for a search in the Victoria & Albert Musuem (V&A) API in a python dictionary. 
    The V&A API offers aggregated statistics on searches. This function provides those statistics in dictionary form.
    This differes from page_summary in that it looks at overall data for a search rather than a single page and also
    provides differing statistics that are unavailible for specific objects.

    Parameters
    ----------
    q : obj
        search query for specific items matching query. 

    Returns
    -------
    dicitonary: dict
        All calculated summary statistics presented in dictionary form. 

    Examples
    --------
    >>> search("Paris")
        75409 matching object records for query Paris:
        {'category': 'Designs',
         'person': 'Worth, Jean-Charles',
         'organisation': 'Worth',
         'collection': 'Prints, Drawings & Paintings Collection',
         'gallery': 'Prints & Drawings Study Room, level E',
         'style': 'French School',
         'place': 'Paris',
         'object_type': 'Fashion design',
         'technique': 'watercolour drawing',
         'material': 'watercolour',
         'maker': 'Worth',
         'associated': 'Louvre (Paris)',
         'depicts': 'Paris',
         'accession_year': '1957'}
    """
    assert type(q) == str, "The query must be of type 'string'"
    try:
        req = requests.get(f'https://api.vam.ac.uk/v2/objects/clusters/search?q={q}')
        object_data = req.json()
        object_info = object_data["info"]
    except KeyError as key_err: 
        print(f'Key error occurred, you must enter a query for this function to work: {key_err}') #raise error for HTTP

    record_count = object_info["record_count"]
    object_clusters = object_data["clusters"]
    print(f"{record_count} matching object records for query {q}:")
    
    keys  = []
    values = []
    for i in object_clusters:
        keys.append(i)
    try:
        for i in object_clusters:
            values.append(object_clusters[i]['terms'][0]["value"])
    except IndexError as index_err:
        print(f"WARNING: One of the categories has an unknown value resulting in a {index_err}")
        
    res = dict(zip(keys,values))
    return(res)
    


# In[13]:


#test search function for assertion error with non-string
def test_search_assertion():
    with pytest.raises(AssertionError):
        search(134)
    


# In[7]:


#test search function page_size parameter works
def test_search_pagesize():
    with mock.patch('builtins.input', return_value="1"): #mock input to 1
        x = search("hello", page_size = 87)
        assert len(x) == 87


# In[8]:


#test page_summary function works
def test_pg_sum():
    with mock.patch('builtins.input', return_value="1"):
        x = page_summary("dortmund")
        assert x["pop_loc"] == "Brussels"


# In[9]:


#test get_images 
def test_get_images():
    with mock.patch('builtins.input', return_value="1"):
        x = get_images("hello", page = 2)
        assert len(x) == 30


# In[10]:


#test cluster summary returns dictionary
def test_cluster():
    with mock.patch('builtins.input', return_value="1"):
        x = cluster_summary("Italy")
        assert type(x) == dict


# In[11]:


#test cluster summary returns correct values
def test_cluster_values():
    with mock.patch('builtins.input', return_value="1"):
        x = cluster_summary("Italy")
        assert x["category"] == "Topography"

