import functools
from numpy import hstack
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from ExcelFileAnalyzer import ExcelFileAnalyzer


def tokenize_data(self, data):
    try:
        tokens = self.okt.morphs(data)
        return ' '.join(tokens)
    except Exception as e:
        print(f"Error tokenizing data: {e}")
        return data

def run_clustering(self, target_column):
    if self._is_df_empty(self.df):
        self.notify("show_error", message="No data found.")
        return
    
    # Preprocessing: Filter out rows with the value "미작성"
    self.df = self.df[self.df[target_column] != "미작성"]
    
    # Tokenizing values in each row of the target column
    self._tokenize_column(target_column)

    # Vectorize the data (normalized length included)
    tfidf_matrix = self._vectorize_data(self.df[f'tokenized_{target_column}'])
    combined_features = self._add_normalized_length(target_column, tfidf_matrix)

    # Repeat the same process until the clustering result is stable

    # 1. 'Opinion' and 'No Opinion'
    self.df['binary_cluster'] = self._apply_binary_clustering(combined_features)
    avg_length_per_cluster = self.df.groupby('binary_cluster')['text_length'].mean()
    opinion_cluster = avg_length_per_cluster.idxmax() 
    self._drop_data_by_cluster('binary_cluster', opinion_cluster)

    # 2. 'Satisfied/Not Satisfied' and 'Opinion'
    tfidf_matrix = self._vectorize_data(self.df[f'tokenized_{target_column}'])
    combined_features = self._add_normalized_length(target_column, tfidf_matrix)
    self.df['binary_cluster'] = self._apply_binary_clustering(combined_features)
    avg_length_per_cluster = self.df.groupby('binary_cluster')['text_length'].mean()
    opinion_cluster = avg_length_per_cluster.idxmax()
    opinion_df, review_df = self._split_data_by_cluster('binary_cluster', opinion_cluster)

    # 3. Subclassification (Good vs. Bad vs. None)
    self._subclassify_reviews(review_df, target_column)
    opinion_df.loc[:, 'category'] = "Opinion"

    # 4. Concatenate the two DataFrames
    self.df_result = pd.concat([review_df, opinion_df], axis=0)
    self.df_result.drop(columns=['law', 'field', 'purpose', 'age', 'answer', 'phone', 'check'], inplace=True)

    # Notify the UI
    self.notify("update_clustering_label", column_name=target_column)
    print("Done executing run_clustering()")

    # Save the result
    print("Saving the result...")
    output_file = f"{self.file_name}_converted.xlsx"
    self.df_result.to_excel(output_file, index=False) 

# Decorators
def log_function_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Executing {func.__name__}...")
        result = func(*args, **kwargs)
        print(f"Finished {func.__name__}.")
        return result
    return wrapper

# Methods called inside run_clustering()
@log_function_call
def _tokenize_column(self, target_column):
    self.df[f'tokenized_{target_column}'] = self.df[target_column].apply(self.tokenize_data)

from sklearn.feature_extraction.text import TfidfVectorizer

@log_function_call
def _add_normalized_length(self, target_column, tfidf_matrix):
    self.df['text_length'] = self.df[target_column].apply(len)
    scaler = MinMaxScaler()
    normalized_lengths = scaler.fit_transform(self.df['text_length'].values.reshape(-1, 1))
    return hstack([tfidf_matrix, normalized_lengths])

@log_function_call
def _apply_binary_clustering(self, combined_features):
    binary_kmeans = KMeans(n_clusters=2, n_init=10, random_state=ExcelFileAnalyzer.SEED)
    return binary_kmeans.fit_predict(combined_features)

@log_function_call
def _drop_data_by_cluster(self, target_to_measure, standard_clustor):
    self.df = self.df[self.df[target_to_measure] == standard_clustor]

@log_function_call
def _split_data_by_cluster(self, target_to_measure, standard_clustor):
    data_standard = self.df[self.df[target_to_measure] == standard_clustor].copy()
    data_not_standard = self.df[self.df[target_to_measure] != standard_clustor].copy()
    return data_standard, data_not_standard

@log_function_call
def _subclassify_reviews(self, review_data, target_column):
    review_data['category'] = self.df[target_column].apply(self._do_subclassification)