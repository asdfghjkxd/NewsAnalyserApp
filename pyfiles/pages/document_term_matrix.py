"""
Document Term Matrix is one of the core modules of this app.

This module is responsible for the creation of a Document-Term Matrix and visualising the Document-Term Matrix.

A large portion of this module uses the nltk and scikit-learn packages to create the Document-Term Matrix document.
"""

# -------------------------------------------------------------------------------------------------------------------- #
# |                                             IMPORT RELEVANT LIBRARIES                                            | #
# -------------------------------------------------------------------------------------------------------------------- #
import os
import pathlib

import openpyxl
import pandas as pd
import plotly.express
import streamlit as st
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
import pandas_profiling
import kaleido

from streamlit_pandas_profiling import st_profile_report
from utils import csp_downloaders
from utils.helper import readFile, printDataFrame

# -------------------------------------------------------------------------------------------------------------------- #
# |                                           GLOBAL VARIABLE DECLARATION                                            | #
# -------------------------------------------------------------------------------------------------------------------- #
STREAMLIT_STATIC_PATH = pathlib.Path(st.__path__[0]) / 'static'
DOWNLOAD_PATH = (STREAMLIT_STATIC_PATH / "downloads")
DTM = pd.DataFrame()
pd.options.plotting.backend = 'plotly'
SIZE = 'Small File(s)'
DATA = pd.DataFrame()
DATA_PATH = None
ANALYSIS = False
VERBOSE_DTM = False
VERBOSITY_DTM = False
VERBOSE_ANALYSIS = False
SAVE = False
MODE = 'CSV'
DTM_copy = pd.DataFrame()
N = 100
DTM_copy_ = pd.DataFrame()
CSP = None
ADVANCED_ANALYSIS = False
FINALISED_DATA_LIST = []
DATA_COLUMN = None
TOP_N_WORD_FIG = None


# -------------------------------------------------------------------------------------------------------------------- #
# |                                             MAIN APP FUNCTIONALITY                                               | #
# -------------------------------------------------------------------------------------------------------------------- #
def app():
    """
    This function is called when the app is run
    """

# -------------------------------------------------------------------------------------------------------------------- #
# |                                                GLOBAL VARIABLES                                                  | #
# -------------------------------------------------------------------------------------------------------------------- #
    global DATA, DATA_PATH, ANALYSIS, VERBOSE_DTM, VERBOSITY_DTM, VERBOSE_ANALYSIS, SAVE, SIZE, MODE, \
        STREAMLIT_STATIC_PATH, DOWNLOAD_PATH, DTM, DTM_copy, N, DTM_copy_, CSP, ADVANCED_ANALYSIS, \
        FINALISED_DATA_LIST, DATA_COLUMN, TOP_N_WORD_FIG

# -------------------------------------------------------------------------------------------------------------------- #
# |                                                     INIT                                                         | #
# -------------------------------------------------------------------------------------------------------------------- #
    if not DOWNLOAD_PATH.is_dir():
        DOWNLOAD_PATH.mkdir()

    st.title('Document-Term Matrix and Word Frequency Analysis')
    st.markdown('## Init\n'
                'Before proceeding, you will need to download the corpus needed to process your data. To do so, click '
                'on the "Begin Download" button below. Please ensure that you have at least 3 GB of free disk space '
                'available so that you are able to download the corpus onto your system and that your device is '
                'connected to the Internet.')
    if st.button('Begin Download', key='download-model'):
        os.system('python -m nltk.downloader all')
    st.markdown('## Upload Data\n'
                'For this mode, ensure that your file is smaller than 200 MB in size. If your file is larger than '
                '200 MB, you may choose to rerun the app with the tag `--server.maxUploadSize=[SIZE_IN_MB_HERE]` '
                'appended behind the `streamlit run app.py` command and define the maximum size of file you can '
                'upload onto Streamlit, or use the Large File option to pull your dataset from any one of the '
                'three supported Cloud Service Providers into the app. Note that modifying the command you use '
                'to run the app is not available if you are using the web interface for the app and you will be '
                'limited to using the Large File option to pull datasets larger than 200 MB in size.\n\n'
                'Also, ensure that your data is cleaned and lemmatized before passing it into this module. If '
                'you have not cleaned your dataset, use the Load, Clean and Visualise module to clean up your '
                'data before proceeding.')
    SIZE = st.selectbox('Define the size of the file to pass into function', ('Small File(s)', 'Large File(s)'))
    MODE = st.selectbox('Define the data input format', ('CSV', ' XLSX'))

# -------------------------------------------------------------------------------------------------------------------- #
# |                                                 FILE UPLOADING                                                   | #
# -------------------------------------------------------------------------------------------------------------------- #
    st.markdown('### Upload the file that you wish to analyse:\n')
    if SIZE == 'Small File(s)':
        DATA_PATH = st.file_uploader(f'Load up a {MODE} File containing the cleaned data', type=[MODE])
        if DATA_PATH is not None:
            DATA = readFile(DATA_PATH, MODE)
            if not DATA.empty or not DATA:
                DATA_COLUMN = st.selectbox('Choose Column where Data is Stored', list(DATA.columns))
                st.success('Data Loaded!')

    elif SIZE == 'Large File(s)':
        st.info(f'File Format Selected: {MODE}')
        CSP = st.selectbox('CSP', ('Select a CSP', 'Azure', 'Amazon', 'Google', 'Google Drive'))

        if CSP == 'Azure':
            azure = csp_downloaders.AzureDownloader()
            if azure.SUCCESSFUL:
                try:
                    azure.downloadBlob()
                    DATA = readFile(azure.AZURE_DOWNLOAD_ABS_PATH, MODE)
                    if not DATA.empty:
                        DATA_COLUMN = st.selectbox('Choose Column where Data is Stored', list(DATA.columns))
                        st.info('File Read!')
                except Exception as ex:
                    st.error(f'Error: {ex}. Try again.')

        elif CSP == 'Amazon':
            aws = csp_downloaders.AWSDownloader()
            if aws.SUCCESSFUL:
                try:
                    aws.downloadFile()
                    DATA = readFile(aws.AWS_FILE_NAME, MODE)
                    if not DATA.empty:
                        DATA_COLUMN = st.selectbox('Choose Column where Data is Stored', list(DATA.columns))
                        st.info('File Read!')
                except Exception as ex:
                    st.error(f'Error: {ex}. Try again.')

        elif CSP == 'Google':
            gcs = csp_downloaders.GoogleDownloader()
            if gcs.SUCCESSFUL:
                try:
                    gcs.downloadBlob()
                    DATA = readFile(gcs.GOOGLE_DESTINATION_FILE_NAME, MODE)
                    if not DATA.empty:
                        DATA_COLUMN = st.selectbox('Choose Column where Data is Stored', list(DATA.columns))
                        st.info('File Read!')
                except Exception as ex:
                    st.error(f'Error: {ex}. Try again.')

        elif CSP == 'Google Drive':
            gd = csp_downloaders.GoogleDriveDownloader()
            if gd.SUCCESSFUL:
                try:
                    gd.downloadBlob()
                    DATA = readFile(gd.GOOGLE_DRIVE_OUTPUT_FILENAME, MODE)
                    if not DATA.empty:
                        DATA_COLUMN = st.selectbox('Choose Column where Data is Stored', list(DATA.columns))
                        st.info('File Read!')
                except Exception as ex:
                    st.error(f'Error: {ex}. Try again.')

# -------------------------------------------------------------------------------------------------------------------- #
# |                                                      FLAGS                                                       | #
# -------------------------------------------------------------------------------------------------------------------- #
    st.markdown('## Flags\n'
                'The following section contains flags you can use to better define the outputs of this module and to '
                'modify what the app prints out to screen.\n\n'
                'Note that there is an inherent size limit (50 MB) for the DataFrames that are printed to screen. If '
                'you get an error telling you that the DataFrame size is too large to proceed, kindly lower the number '
                'of data points you wish to visualise or download the file and visualise it through Excel or any other '
                'DataFrame visualising Python packages. There is no definitive way to increase the size of the '
                'DataFrame that can be printed out due to the inherent limitation on the size of the packets sent '
                'over to and from the Streamlit server.')
    SAVE = st.checkbox('Save Output DataFrame into CSV File?')
    ANALYSIS = st.checkbox('Conduct Analysis on the Document-Term Matrix?')
    if ANALYSIS:
        VERBOSE_DTM = st.checkbox('Display DataFrame of Document-Term Matrix?')
        if VERBOSE_DTM:
            VERBOSITY_DTM = st.slider('Data points to display for Document-Term Matrix?',
                                      min_value=1,
                                      max_value=1000,
                                      value=20)
        ADVANCED_ANALYSIS = st.checkbox('Display Advanced DataFrame Statistics?')
        VERBOSE_ANALYSIS = st.checkbox('Display top N words in Document-Term Matrix?')
        if VERBOSE_ANALYSIS:
            N = st.slider('Key in the top N number of words to display',
                          key='N',
                          min_value=1,
                          max_value=1000,
                          value=100)

# -------------------------------------------------------------------------------------------------------------------- #
# |                                            DOCUMENT-TERM MATRIX CREATION                                         | #
# -------------------------------------------------------------------------------------------------------------------- #
    st.markdown('## Analysis Operation\n'
                'Ensure that you have successfully uploaded the data and selected the correct field for analysis '
                'before proceeding.')
    if st.button('Proceed', key='doc'):
        if not DATA.empty:
            DATA = DATA.astype(str)
            with st.spinner('Working to create a Document-Term Matrix...'):
                counter_object = CountVectorizer(stop_words=stopwords.words('english'))

                # CONCATENATE ALL STR VALUES INTO LIST: OPTIMISED
                word_string = ' '.join(DATA[DATA_COLUMN])

                # CREATE A NEW DF TO PARSE
                dict_data = {
                    'text': word_string
                }
                series_data = pd.DataFrame(data=dict_data, index=[0])

                # FIT-TRANSFORM THE DATA
                series_data = counter_object.fit_transform(series_data.text)

                # CONVERT THE FITTED DATA INTO A PANDAS DATAFRAME TO USE FOR THE DTMs
                DTM = pd.DataFrame(series_data.toarray(),
                                   columns=counter_object.get_feature_names(),
                                   index=[0])

# -------------------------------------------------------------------------------------------------------------------- #
# +                                                 VISUALISE THE DATA                                               + #
# -------------------------------------------------------------------------------------------------------------------- #
            if not DTM.empty:
                if ANALYSIS:
                    if VERBOSE_DTM:
                        # VISUALISE THE DATA
                        st.markdown('## Visualise Data\n'
                                    'The Document-Term Matrix will now be displayed on screen.')
                        DTM_copy = DTM.copy()
                        try:
                            st.dataframe(DTM_copy.head(N), width=900, height=500)
                        except RuntimeError:
                            st.warning('Warning: Size of DataFrame is too large. Defaulting to 10 data points...')
                            st.dataframe(DTM_copy.head(10), height=600, width=800)
                        except Exception as ex:
                            st.error(f'Error: {ex}')

                    if VERBOSE_ANALYSIS:
                        DTM_copy_ = DTM.copy().transpose()
                        DTM_copy_.columns = ['Word Frequency']
                        DTM_copy_.sort_values(by=['Word Frequency'], ascending=False, inplace=True)
                        st.markdown('The following DataFrame contains the sorted Document-Term Matrix, '
                                    f'displaying the top {N} words of the Document-Term Matrix.')
                        printDataFrame(data=DTM_copy_, verbose_level=VERBOSITY_DTM, advanced=ADVANCED_ANALYSIS)
                        TOP_N_WORD_FIG = DTM_copy_.head(N).plot.line(title=f'Frequency of top {N} words used',
                                                                     labels=dict(index='Word',
                                                                                 value='Frequency',
                                                                                 variable='Count'),
                                                                     width=900,
                                                                     height=500)
                        st.plotly_chart(TOP_N_WORD_FIG, use_container_width=True)

                FINALISED_DATA_LIST = [
                    (DTM, 'DTM', 'dtm.csv', 'csv'),
                    (DTM_copy_, 'Sorted DTM', 'sorted_dtm.csv', 'csv'),
                    (TOP_N_WORD_FIG, f'Top {N} Words Frequency', 'top_n.png', 'png')
                ]

# -------------------------------------------------------------------------------------------------------------------- #
# +                                                   SAVE THE DATA                                                  + #
# -------------------------------------------------------------------------------------------------------------------- #
                if SAVE:
                    st.markdown('## Download Data')
                    for data in FINALISED_DATA_LIST:
                        if data[3] == 'csv':
                            if not data[0].empty:
                                st.markdown(f'### {data[1]}')
                                st.markdown(f'Download requested data from [downloads/{data[2]}]'
                                            f'(downloads/{data[2]})')
                                data[0].to_csv(str(DOWNLOAD_PATH / data[2]), index=False)
                        elif data[3] == 'png':
                            if data[0]:
                                st.markdown(f'### {data[1]}')
                                st.markdown(f'Download requested data from [downloads/{data[2]}]'
                                            f'(downloads/{data[2]})')
                                data[0].write_image(str(DOWNLOAD_PATH / data[2]))
        else:
            st.error('Error: No files are loaded.')
