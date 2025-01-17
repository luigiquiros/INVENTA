import pandas as pd
import numpy as np
import zipfile
import os
import scipy as sp
import matplotlib.pyplot as plt
import plotly.express as px
import zipfile
import pathlib
from tqdm import tqdm

def quant_table(quantitative_data_filename, data_process_origin, use_ion_dentity):
    """ Cleans up the quantitative table to specific format

    Args:
        df = quantitative.csv file, output from MZmine

    Returns:
        None
    """
    #read the file 

    df = pd.read_csv(quantitative_data_filename, sep=',')#,  index_col='row ID')
    df.rename(columns = lambda x: x.replace(' Peak area', ''),inplace=True)
    df.drop(list(df.filter(regex = 'Unnamed:')), axis = 1, inplace = True)
    df.sort_index(axis=1, inplace=True)

    if data_process_origin == 'MZMine3':

        if use_ion_dentity == True:

            df.drop(['row ion mobility', 'row m/z', 'row retention time',
                'row ion mobility unit', 'row CCS', 'best ion',
                'correlation group ID', 'auto MS2 verify',
                'identified by n=', 'partners', 'neutral M mass'], axis=1, inplace=True)

            #complete correlation groups
            df['annotation network number'] = df['annotation network number'].fillna(df['row ID'].apply(str) + 'x')
            df.drop('row ID', axis =1, inplace=True)
            df = df.groupby('annotation network number', dropna=False).max()

        else:
            #prepare quant table acordingly 

            df.drop('row m/z', axis=1, inplace=True)
            df.drop('row retention time', axis=1, inplace=True)

            df.drop(['row ion mobility', 'correlation group ID', 'best ion', 'row ion mobility unit', 'row CCS', 
            'annotation network number', 'auto MS2 verify', 'identified by n=', 'partners', 'neutral M mass'], axis=1, inplace=True)
            df.set_index('row ID', inplace=True)

    else:
        df 

    if data_process_origin == 'MZMine2':  

        df.drop('row m/z', axis=1, inplace=True)
        df.drop('row retention time', axis=1, inplace=True)
        df.set_index('row ID', inplace=True)

    else:
        df
    df = df.apply(lambda x: x/x.max(), axis=0)

    return df

def correlation_groups(quantitative_data_filename, use_ion_dentity):
    #recover metadata information for each correlation group
    if use_ion_dentity == True:
        
        df = pd.read_csv(quantitative_data_filename, sep=',')#,  index_col='row ID')
        df.rename(columns = lambda x: x.replace(' Peak area', ''),inplace=True)
        df.drop(list(df.filter(regex = 'Unnamed:')), axis = 1, inplace = True)
        df.drop(['row ion mobility', ''
            'row ion mobility unit', 'row CCS', 
            'correlation group ID', 'auto MS2 verify',
            'identified by n=', 'partners'], axis=1, inplace=True)
        df.rename(columns={'best ion': 'adduct (ion identity)', 'neutral M mass':'neutral mass (ion identity)', 'row retention time':'retention time (min)' }, inplace=True)
        #complete correlation groups
        df['annotation network number'] = df['annotation network number'].fillna(df['row ID'].apply(str) + 'x')
        #df = df.reset_index()
        #agg_func = {'row retention time': 'mean', 'row m/z': 'max',  'adduct': set, 'row ID': set}
        #df = df.groupby('correlation group ID', as_index=False).agg(agg_func)  
        df = df.iloc[:, :6]
        return df 

    else: 
        print('ion identity not used')
    
def get_gnps_annotations(df):
    #retrive the clusterinfosummary file from the gnps jod downloaded before
    
    for filepath in pathlib.Path("../data/all_annotation/clusterinfo_summary/").glob('**/*'):
        filepath.absolute()
    
    df_network = pd.read_csv(filepath.absolute(),
                                sep='\t', 
                                usecols =['cluster index', 'componentindex'])
    df = pd.merge(df_network[['cluster index', 'componentindex']], df,left_on= 'cluster index', right_on='#Scan#', how='left')
    df.to_csv('../data_out/annot_gnps_df.tsv', sep='\t')
    return df

def get_isdb_annotations(path_isdb, isdb_annotations): 
    
    if isdb_annotations == True:
        df = pd.read_csv(path_isdb,
                                sep='\t', 
                                usecols =['feature_id','molecular_formula','score_final','score_initialNormalized'], 
                                low_memory=False)
        return df 
    else: 
        print('The isdb annotations output will be not used')

def get_sirius_annotations(path_sirius, sirius_annotations): 

    if sirius_annotations == True:
        df = pd.read_csv(path_sirius,
                                sep='\t', 
                                usecols =['id','ConfidenceScore','ZodiacScore'], 
                                low_memory=False)
        return df 
    else: 
        print('The sirius annotations will be not used')

def get_canopus_pred_classes(path_canopus, CC_component): 

    if CC_component == True:
        df = pd.read_csv(path_canopus, sep='\t')
        df['shared name'] = df['id'].str.split('_').str[-1].astype(int)
        return df 
    else: 
        print('The canopus classes will be not used')

def get_metadata_ind_files(repository_path):
    """
    Function to recover the metadata from individual files, used for calculation of inventa non aligned data
    """
    path = os.path.normpath(repository_path)
    samples_dir = [directory for directory in os.listdir(path)]
    
    df= pd.DataFrame()
    for directory in tqdm(samples_dir):
        metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
    
        try:
            metadata_df = pd.read_csv(metadata_path, sep='\t')
        except FileNotFoundError:
            continue
        except NotADirectoryError:
            continue

   
        metadata_df = pd.read_csv(metadata_path, sep='\t')
        df = df.append(metadata_df)#, ignore_index=True)
        #df.drop(list(df.filter(regex = 'Unnamed:')), axis = 1, inplace = True)
    
    pathout = os.path.join(path, 'results/')
    os.makedirs(pathout, exist_ok=True)
    pathout = os.path.join(pathout, 'Metadata_combined.tsv')
    df.to_csv(pathout, sep ='\t')

    return df

def load_metric_df(repository_path, ionization_mode):
    
    path = os.path.normpath(repository_path)
    samples_dir = [directory for directory in os.listdir(path)]

    for directory in tqdm(samples_dir):

        MEMO_path1 = os.path.join(path +'/results/', 'memo_matrix_filtered' +'_'+ ionization_mode + '.tsv')
        MEMO_path2 = os.path.join(path +'/results/', 'memo_matrix_non_filtered' +'_'+ ionization_mode + '.tsv')

        try:
            df1 = pd.read_csv(MEMO_path1, sep='\t')
            df2 = pd.read_csv(MEMO_path2, sep='\t')

        except FileNotFoundError:
            continue
        except NotADirectoryError:
            continue

    if os.path.isfile(MEMO_path1):
        df =  pd.read_csv(MEMO_path1, sep='\t')
    else:
        df = pd.read_csv(MEMO_path2, sep='\t')
    return df