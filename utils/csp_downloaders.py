"""
This module is used for the downloading of the files from the major CSPs.
"""
# -------------------------------------------------------------------------------------------------------------------- #
# |                                         IMPORT RELEVANT LIBRARIES                                                | #
# -------------------------------------------------------------------------------------------------------------------- #
import os
import io
import shutil

import boto3
import botocore
import pandas as pd
import streamlit as st
from azure.storage.blob import BlobServiceClient
from google.cloud import storage


# -------------------------------------------------------------------------------------------------------------------- #
# |                                                     AWS                                                          | #
# -------------------------------------------------------------------------------------------------------------------- #
class AWSDownloader:
    """
    This class manages the downloading of files stored on AWS

    This class only permits you to download files from a blob, one at a time. No threading is enabled on this class.

    Global Variables
    ----------------
    AWS_ACCESS_KEY_ID:                  The Access Key ID that is generated by AWS when creating a new user in the
                                        Management Console
    AWS_SECRET_ACCESS_KEY:              The Secret Access Key that is generated by AWS when creating a new user in the
                                        Management Console, is found on the same page as AWS_ACCESS_KEY_ID
    AWS_CREDENTIAL_FILE:                A CSV file containing the credentials for the AWS account
    AWS_BUCKET_NAME:                    The name of the bucket which the data is stored
    AWS_OBJECT_KEY:                     The object key to the bucket
    AWS_FILE_NAME:                      The filename of the file of interest
    ----------------
    """

    def __init__(self):
        """
        Establishes a connection with AWS and authenticates the user
        """

        # DEFINE CLASS SPECIFIC VARIABLES
        self.AWS_ACCESS_KEY_ID = ''
        self.AWS_SECRET_ACCESS_KEY = ''
        self.AWS_CREDENTIAL_FILE = None
        self.AWS_BUCKET_NAME = ''
        self.AWS_OBJECT_KEY = ''
        self.AWS_FILE_NAME = os.path.join(os.getcwd(), 'file.csv')
        self.s3Session = boto3.resource('s3')
        self.SUCCESSFUL = False

        st.title('AWS Downloader')
        self.FROM_CREDENTIAL_FILE = st.checkbox('Input Credentials in the form of CSV format?')

        with st.form('AWS Parameters'):
            if self.FROM_CREDENTIAL_FILE:
                self.AWS_CREDENTIAL_FILE = st.file_uploader('Upload Credential File', type=['CSV'],
                                                            help='Upload a CSV file downloaded from AWS containing '
                                                                 'your credentials for your S3 Storage Account')
            else:
                self.AWS_ACCESS_KEY_ID = st.text_input('AWS Access Key')
                self.AWS_SECRET_ACCESS_KEY = st.text_input('AWS Secret Access Key')

            self.AWS_BUCKET_NAME = st.text_input('Bucket Name', help='This is the name of the S3 bucket you have '
                                                                     'created')
            self.AWS_OBJECT_KEY = st.text_input('S3 Object Key', help='This is the name of the file you want to pull '
                                                                      'from your S3 bucket. It should contain the '
                                                                      'relative path to the file (if your file is '
                                                                      'not found in the root directory)')
            self.AWS_FILE_NAME = st.text_input('Filename with extension; note that the file will always be '
                                               'saved in the current working directory',
                                               help='If file extensions are not included, your file will not be able '
                                                    'to load. If you encounter errors, ensure that the file extension '
                                                    'is present and correct; no file extension validation is done '
                                                    'on the files you decide to pull')
            self.SUBMIT = st.form_submit_button('Submit Parameters')

            if self.SUBMIT:
                if self.FROM_CREDENTIAL_FILE and not self.AWS_CREDENTIAL_FILE and not self.AWS_BUCKET_NAME and not \
                        self.AWS_OBJECT_KEY and not self.AWS_FILE_NAME:
                    st.error('Error: Parameters are not loaded or is validated successfully. Try again.')
                    self.SUCCESSFUL = False
                elif not self.FROM_CREDENTIAL_FILE and not self.AWS_CREDENTIAL_FILE and not self.AWS_BUCKET_NAME and \
                        not self.AWS_OBJECT_KEY and not self.AWS_FILE_NAME:
                    st.error('Error: Parameters are not loaded or is validated successfully. Try again.')
                    self.SUCCESSFUL = False
                else:
                    try:
                        temp_df = pd.read_csv(self.AWS_CREDENTIAL_FILE)
                    except Exception as e:
                        st.error(f'Error: {e}')
                    else:
                        self.AWS_ACCESS_KEY_ID = str(temp_df['Access key ID'][0])
                        self.AWS_SECRET_ACCESS_KEY = str(temp_df['Secret access key'][0])

                        os.environ['AWS_ACCESS_KEY_ID'] = self.AWS_ACCESS_KEY_ID
                        os.environ['AWS_SECRET_ACCESS_KEY'] = self.AWS_SECRET_ACCESS_KEY

                        self.SUCCESSFUL = True
                        st.info('Credentials Loaded!')

    def downloadFile(self):
        """
        File downloader
        """

        if self.SUCCESSFUL:
            try:
                self.s3Session.Bucket(self.AWS_BUCKET_NAME).download_file(self.AWS_OBJECT_KEY, self.AWS_FILE_NAME)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '401':
                    st.error('User Unauthorised. Ensure that your credentials are correct before submitting the form.')
                elif e.response['Error']['Code'] == '403':
                    st.error('User Unauthorised. Ensure that your credentials permit you to view and download the '
                             'requested file from the S3 bucket.')
                elif e.response['Error']['Code'] == '404':
                    st.error('File does not exist.')
            else:
                st.success(f'File {self.AWS_FILE_NAME} Downloaded!')
        else:
            st.error('Error: Parameters are not loaded or is validated successfully. Try again.')


# -------------------------------------------------------------------------------------------------------------------- #
# |                                                   AZURE                                                          | #
# -------------------------------------------------------------------------------------------------------------------- #
class AzureDownloader:
    """
    This class manages the downloading of files stored on Azure

    This class also allows you to download just one blob or all blobs stored in your container on Azure Storage

    Global Variables
    ----------------
    AZURE_CONNECTION_STRING:        Azure Storage Account Connection String
    AZURE_BLOB_NAME:                Name of Azure Storage Account Blob where data is stored
    LOCAL_DOWNLOAD_PATH:            Local Folder where downloaded data is stored
    AZURE_DOWNLOAD_PATH:            Local Folder path combined with the name of the file, None by default unless User
                                    specifies
    AZURE_DOWNLOAD_ABS_PATH:        Final Destination of the files downloaded
    SUCCESSFUL:                     Flag
    ----------------
    """

    def __init__(self):
        """
        This establishes connection with Azure and defines important ((environment)) variables that is necessary for
        the connection to be open and maintained for the download
        """

        # DEFINE CLASS SPECIFIC VARIABLES
        self.AZURE_CONNECTION_STRING = ''
        self.AZURE_BLOB_NAME = ''
        self.LOCAL_DOWNLOAD_PATH = os.getcwd()
        self.AZURE_DOWNLOAD_PATH = os.getcwd()
        self.AZURE_DOWNLOAD_ABS_PATH = None
        self.SUCCESSFUL = False

        st.title('Azure Downloader')
        with st.form('API Variables'):
            st.markdown('Due to limitations of the API and how data stored in Azure Blobs, when this method is called, '
                        'all files in a blob is downloaded. Ensure that you only have **one** file per blob to avoid '
                        'this error.')
            self.AZURE_CONNECTION_STRING = st.text_input("Azure Connection String")
            self.AZURE_BLOB_NAME = st.text_input("Azure Blob Name")
            self.LOCAL_DOWNLOAD_PATH = st.text_input("Local Download Path (do not modify if running on web app)",
                                                     value=os.path.join(os.getcwd()))
            self.SUBMIT = st.form_submit_button('Submit Parameters')

            if self.SUBMIT:
                if not self.AZURE_CONNECTION_STRING or not self.AZURE_BLOB_NAME or not self.LOCAL_DOWNLOAD_PATH:
                    st.error('Error: Parameters are not loaded or is validated successfully. Try again.')
                    self.SUCCESSFUL = False
                else:
                    st.success('Parameters Validated and Accepted!')
                    self.SUCCESSFUL = True

                    try:
                        self.BlobServiceClient_ = BlobServiceClient.from_connection_string(self.AZURE_CONNECTION_STRING)
                        self.ClientContainer = self.BlobServiceClient_.get_container_client(self.AZURE_BLOB_NAME)
                        st.success('Connection Established!')
                    except Exception as e:
                        st.error(f'Error: {e}')
                        return

    def saveBlob(self, filename, file_content):
        """
        Writes the blob content into a file

        Parameters
        ----------
        filename:            Name of the file stored in the blob
        file_content:        Contents of the files stored in the blob
        ----------
        """

        if self.SUCCESSFUL:
            # FULL FILEPATH
            self.AZURE_DOWNLOAD_PATH = os.path.join(self.LOCAL_DOWNLOAD_PATH, filename)

            # MAKE DIR FOR NESTED BLOBS
            os.makedirs(os.path.dirname(self.AZURE_DOWNLOAD_PATH), exist_ok=True)

            # WRITE OUT
            with open(self.AZURE_DOWNLOAD_PATH, 'wb') as azfile:
                azfile.write(file_content)
        else:
            st.error('Error: Parameters are not loaded or is validated successfully. Try again.')

    def downloadBlob(self):
        """
        Downloads the blob and writes out the name
        """

        if self.SUCCESSFUL:
            ClientBlob = self.ClientContainer.list_blobs()

            for blob in ClientBlob:
                print('.', end='')
                byte = self.ClientContainer.get_blob_client(blob).download_blob().readall()
                print(byte)
                self.saveBlob(blob.name, byte)
                # self.AZURE_DOWNLOAD_ABS_PATH = os.path.join(self.AZURE_DOWNLOAD_PATH, blob.name)
                st.success('File Successfully downloaded!')
        else:
            st.error('Error: Parameters are not loaded or is validated successfully. Try again.')


# -------------------------------------------------------------------------------------------------------------------- #
# |                                                    GCC                                                           | #
# -------------------------------------------------------------------------------------------------------------------- #
class GoogleDownloader:
    """
    This class manages the downloading of files stored on Google Cloud

    This class only permits you to download files from a blob, one at a time. No threading is enabled on this class.

    Global Variables
    ----------------
    GOOGLE_APPLICATION_CREDENTIALS:                 Represents the path to the JSON file containing the credentials
    GOOGLE_BUCKET_NAME:                             Name of your GCS bucket
    GOOGLE_STORAGE_OBJECT_NAME:                     Name of the file you stored in the GCC bucket
    GOOGLE_DESTINATION_FILE_NAME:                   Path of the downloaded file, defaults to Current Working Directory
    SUCCESSFUL                                      Flag
    ----------------
    """

    def __init__(self):
        self.GOOGLE_APPLICATION_CREDENTIALS = None
        self.GOOGLE_BUCKET_NAME = ''
        self.GOOGLE_STORAGE_OBJECT_NAME = ''
        self.GOOGLE_DESTINATION_FILE_NAME = os.path.join(os.getcwd(), self.GOOGLE_STORAGE_OBJECT_NAME)
        self.SUCCESSFUL = False

        st.title('Google Downloader')

        with st.form('API Variables'):
            self.GOOGLE_APPLICATION_CREDENTIALS = st.file_uploader('Load Service Account Credentials', type=['JSON'])
            self.GOOGLE_BUCKET_NAME = st.text_input('ID of GCC Bucket')
            self.GOOGLE_STORAGE_OBJECT_NAME = st.text_input('ID of GCC Object')
            self.GOOGLE_DESTINATION_FILE_NAME = os.path.join(os.getcwd(), st.text_input('Downloaded Filename (with '
                                                                                        'extensions). The file will '
                                                                                        'always be downloaded to the '
                                                                                        'current working directory.'))
            self.SUBMIT = st.form_submit_button('Submit Parameters')

            if self.SUBMIT:
                if not self.GOOGLE_BUCKET_NAME or not self.GOOGLE_STORAGE_OBJECT_NAME or not \
                        self.GOOGLE_DESTINATION_FILE_NAME or not self.GOOGLE_APPLICATION_CREDENTIALS:
                    st.error('Error: Parameters are not loaded or is validated successfully. Try again.')
                    self.SUCCESSFUL = False
                else:
                    st.success('Parameters Validated and Accepted!')

                    try:
                        st.info('Loading Credentials...')
                        self.GOOGLE_APPLICATION_CREDENTIALS.seek(0)
                        with open('google_credentials.json', 'wb') as f:
                            shutil.copyfileobj(self.GOOGLE_APPLICATION_CREDENTIALS, f)
                        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.getcwd(),
                                                                                    'google_credentials.json')

                        # INIT STORAGE CLIENT OBJECT
                        self.GoogleClient = storage.Client()
                        self.GoogleBucket = None
                        self.GoogleBlob = None
                    except Exception as e:
                        st.error(e)
                    else:
                        self.SUCCESSFUL = True
                        st.success('Successfully loaded!')

    def downloadBlob(self):
        """
        Downloads the file from the specified Google Cloud storage blob
        """
        if self.SUCCESSFUL:
            try:
                self.GoogleBucket = self.GoogleClient.bucket(self.GOOGLE_BUCKET_NAME)
                self.GoogleBlob = self.GoogleBucket.blob(self.GOOGLE_STORAGE_OBJECT_NAME)
                self.GoogleBlob.download_to_filename(self.GOOGLE_DESTINATION_FILE_NAME)
            except Exception as e:
                self.SUCCESSFUL = False
                st.error(e)
            else:
                st.success('File Downloaded!')
        else:
            st.error('Error: Parameters are not loaded or is validated successfully. Try again.')
