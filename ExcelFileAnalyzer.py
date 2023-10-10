import os
import threading
import pandas as pd
import inspect
import functools
import logging
from datetime import datetime
from inspect import currentframe, getframeinfo
from GPTHandler import GPTHandler
from Observable import Observable
from konlpy.tag import Okt

class ExcelFileAnalyzer(Observable):

    # Constants
    SEED = 42
    INDEX = 'no'
        
    def __init__(self):
        super().__init__()
        self.df = None
        self.df_original = None
        self.filepath = None
        self.filename = None
        self.target_column = None
        self.eval_column = None
        self.excel_files = [None, None]
        self.okt = Okt()
        self.logger = None
        self.file_handler = None
        self.now = datetime.now()

        self._setup_logger()

    def _setup_logger(self, filename=None):

        if(filename is None):
            filename = f"{self.now.strftime('%Y%m%d-%H_%M_%S')}_log.txt"

        # Initialize self.logger if it doesn't exist
        if not hasattr(self, 'logger') or self.logger is None:
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.CRITICAL)

        # Check if there's already an existing file handler and remove it
        if hasattr(self, 'file_handler') and self.file_handler:
            self.logger.removeHandler(self.file_handler)
            self.file_handler.close()
        
        self.file_handler = logging.FileHandler(filename=filename, mode='w')
        self.file_handler.setLevel(logging.CRITICAL)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        self.file_handler.setFormatter(formatter)
        
        self.logger.addHandler(self.file_handler)

    def _change_log_context(self, context):
        logging.critical(f"Program context changed to {context}")

    # Decorators
    def log_function_call(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # print(f"Calling function {func.__name__} with args={args} and kwargs={kwargs}")
            print(f"Calling function {func.__name__}...")
            return func(*args, **kwargs)
        return wrapper
    
    # Helper methods
    def _call_notify_and_logging_error(self, function_name, line_number, error):
        self.notify("show_error", message=f"{function_name} (line {line_number}): An error occurred while reading the file: {error}")
        print(f"{function_name} (line {line_number}): An error occurred while reading the file: {error}")

    def _is_df_empty(self, df=None):
        if df is None:
            return True
        return df.empty
    
    # Open the excel file
    @log_function_call
    def open_excel_file(self):
        excel_file = self.notify("request_excel_file")
        # Read the excel file
        if excel_file:
            try:
                self.df_original = pd.read_excel(excel_file, engine='openpyxl')
                self.df = self.df_original.copy()
                self.filepath = excel_file
                self.file_name = os.path.basename(excel_file)
                self._change_log_context(f"open_excel_file({self.file_name})")
                self.notify("update_content_label", file_name=self.file_name)
            except FileNotFoundError:
                self.notify("show_error", message=f"File '{excel_file}' not found.")
            except Exception as e:
                frameinfo = getframeinfo(currentframe()) # debugging
                self._call_notify_and_logging_error(self, inspect.currentframe().f_code.co_name, frameinfo.lineno,)

        # Set the column names
        if self._is_df_empty(self.df):
            self.notify("show_error", message="No file selected.")
            return
        self.notify("set_column_names", column_names=self.df.columns.values.tolist())
    
    # TODO: Add a method to kill the threads running in GPTHandler
    @log_function_call
    def clear_classify(self):
        self.df = None
        self.df_original = None
        self.filepath = None
        self.file_name = None
        self.target_column = None
        self.eval_column = None
        self.excel_files = [None, None]
        self.notify("update_content_label", file_name="No file selected")
        self.notify("update_save_label", message="Not saved yet")
        self.notify("update_gpt_classification_label", message="Not processed yet")
        self.notify("update_save_label", message="Not saved yet")
        self.notify("set_column_names", column_names=[])
        self.notify("set_num_chunks", num_chunks=0)
        self.notify("set_processed_chunks", processed_chunks=0)
        GPTHandler.clear()

    @log_function_call
    def clear_combine(self):
        self.excel_files = [None, None]
        self.notify("update_combine_0_excel_label", file_name="No file")
        self.notify("update_combine_1_excel_label", file_name="No file")

    # TODO: According to the system message, classify the content
    @log_function_call
    def message_resolver(self, target_column, gpt_message):
        if target_column is None or len(target_column) == 0:
            self.notify("show_error", message="No target column selected.")
            return
        
        self.target_column = target_column
                        
        # TODO: Remove hard-coded values
        if gpt_message == "create category (of 4 types)":
            self._start_threaded_run_gpt_classification(gpt_message)

        elif gpt_message == "evaluate category":
            self.eval_column = "category" # TODO: Remove hard-coded values
            self._start_threaded_run_gpt_classification(gpt_message)

        elif gpt_message == "summarize opinion":
            self.eval_column = "category" # TODO: Remove hard-coded values
            self._start_summarization(gpt_message)

    @log_function_call
    def combine_two_excel_files(self, mode='none', num=-1, base_df=None, extra_df=None):

        if mode == 'open file':
            excel_file = self.notify("request_excel_file")
            if excel_file:
                if num == 0 or 1: # TODO: Remove hard-coded values
                    self.excel_files[num] = excel_file
                    file_name = os.path.basename(excel_file)
                    self.notify(f"update_combine_{num}_excel_label", file_name=file_name)
                return
            else:
                self.notify("show_error", message="No file selected.")
                return

        if mode != 'df ready' and len(self.excel_files) < 2:
            self.notify("show_error", message="There are less than two files in the list.")
            return # TODO: Show a message that there's only one file in the list

        # Load the dataframes (if called from the classificaiton method, the dataframes are already loaded)
        if mode != 'df ready':
            base_df = pd.read_excel(self.excel_files[0], engine='openpyxl')
            extra_df = pd.read_excel(self.excel_files[1], engine='openpyxl')
            self._change_log_context(f"Combine two excel files: ({os.path.basename(self.excel_files[0])} and {os.path.basename(self.excel_files[1])})")
        elif mode == 'df ready':
            self._change_log_context(f"Combine ({self.file_name}) into origianl file (after GPT classification or summarization)")
            
        # Check if the two dataframes match
        self._check_two_excel_files_match(base_df, extra_df)

        # Identify overlapping columns excluding 'index' and drop them from the extra dataframe
        overlapping_columns = [col for col in base_df.columns if col in extra_df.columns and col != ExcelFileAnalyzer.INDEX]
        extra_df = extra_df.drop(columns=overlapping_columns)
    
        # Merge and save the dataframes
        combined_df = base_df.merge(extra_df, on=ExcelFileAnalyzer.INDEX, how='left')

        if mode == 'df ready':
            return combined_df
        
        combined_file_name = f"Combined({os.path.basename(self.excel_files[0])}_{os.path.basename(self.excel_files[1])}).xlsx"
        combined_df.to_excel(combined_file_name, index=False, engine='openpyxl')

        print(f"{combined_file_name} saved successfully.")

    # TODO: Concatenate multiple excel files
    @log_function_call
    def concatenate_excel_files(self):
        excel_files = self.notify("request_mutiple_excel_files")

        if not excel_files:
            return
        
        excel_files_names = [os.path.splitext(os.path.basename(excel_file))[0] for excel_file in excel_files]
        sorted_files_names = sorted(excel_files_names, key=lambda x: int(x.split(".")[0]))

        # Sort the actual file paths by their filenames
        sorted_files = sorted(excel_files, key=lambda x: os.path.basename(x).split(".")[0])

        # Initialize the base dataframe using the first file
        base_df = pd.read_excel(sorted_files[0], engine='openpyxl')
        base_df.insert(0, 'date', sorted_files_names[0])  # Add the filename as the first column

         # Process the rest of the files
        for i, excel_file in enumerate(sorted_files[1:], start=1):
            df_tmp = pd.read_excel(excel_file, engine='openpyxl')
            df_tmp.insert(0, 'date', sorted_files_names[i])  # Add the filename as the first column
            base_df = pd.concat([base_df, df_tmp])
        
        base_df.to_excel(f"Concatenated({sorted_files_names[0]}_{sorted_files_names[-1]}).xlsx", index=False, engine='openpyxl')

    # Private methods

    @log_function_call
    def _check_two_excel_files_match(self, base_df, extra_df, common_column='no', target_column='opinion'):
        # Ensure the target column exists in both dataframes
        if target_column not in base_df.columns or target_column not in extra_df.columns:
            self.notify("show_error", message=f"Column '{target_column}' not found in one or both dataframes.")
            return

        common_indices = base_df[common_column][base_df[common_column].isin(extra_df[common_column])]

        for idx in common_indices:
            base_opinion = base_df.loc[base_df[common_column] == idx, target_column].values[0]
            extra_opinion = extra_df.loc[extra_df[common_column] == idx, target_column].values[0]
            if base_opinion != extra_opinion:
                logging.critical(f"Opinion mismatch at index {idx}.")

    @log_function_call
    def _start_summarization(self, gpt_message):
        if self.eval_column not in self.df.columns.values.tolist():
            self.notify("show_error", message="There are empty cells in the target column.")
            return
        self.df = self.df[self.df[self.eval_column] == '의견']
        self._start_threaded_run_gpt_classification(gpt_message)

    @log_function_call
    def _start_threaded_run_gpt_classification(self, gpt_message):
        self.notify("clicked_gpt_classification_bt", message="Initiate GPT-Powered Classification...")
        # Note: In Python, a single-element tuple must be followed by a comma ,
        #       When you pass gpt_message without a trailing comma, it doesn't create a tuple.
        thread = threading.Thread(target=self._run_gpt_classification, args=(gpt_message,))
        thread.daemon = True
        thread.start()
    
    @log_function_call
    def _run_gpt_classification(self, gpt_message):

        # Create a list of data
        data_structs = [(idx, target, eval) if self.eval_column else (idx, target) for idx, target, eval 
                        in zip(self.df[ExcelFileAnalyzer.INDEX], self.df[self.target_column], self.df.get(self.eval_column, [None] * len(self.df)))]

        # Chunk the tuples based on a token count
        chunks = GPTHandler.get_chunked_tuples(data_structs, gpt_message)
        self.notify("set_num_chunks", num_chunks=len(chunks))

        # Start the threaded process
        response_list = GPTHandler.start_threaded_get_response(chunks, gpt_message, lambda **kwargs: self.notify("set_processed_chunks", **kwargs))

        # Process the result
        self._create_new_column_for_classification(response_list) # TODO: Handle the case where there's already a column named 'category'
        
        # log any missing values
        # TODO: Remove hard-coded values
        if gpt_message == "create category (of 4 types)" or gpt_message == "evaluate category":
            self._compare_num_rows(self.df_original, self.df, "opinion", f"{self.file_name}_log.txt")
        elif gpt_message == "summarize opinion":
            self._compare_num_rows(self.df_original[self.df_original[self.eval_column] == '의견'], self.df, "category", f"{self.file_name}_log.txt")

        combined_df = self.combine_two_excel_files(mode='df ready', base_df=self.df_original, extra_df=self.df)
        
        # Save the result
        combined_df.to_excel(f"GPT_{self.file_name}", index=False)
        self.notify("update_save_label", message="Saved!")

        # Clear the data
        self._clear_result()

    @log_function_call
    def _clear_result(self):
        self.df = self.df_original.copy()
        self.notify("set_num_chunks", num_chunks=0)
        self.notify("set_processed_chunks", processed_chunks=0)
        GPTHandler.clear()

    # Compare the number of rows in a specific column
    @log_function_call
    def _compare_num_rows(self, df_to_be_compared, df_to_compare, col_name, output_filename="log.txt"):
        if df_to_be_compared[col_name].shape[0] != df_to_compare[col_name].shape[0]:
            with open(output_filename, 'a') as log_file:
                log_file.write(f"Original DataFrame has {df_to_be_compared[col_name].shape[0]} rows in column {col_name}.\n")
                log_file.write(f"Converted DataFrame has {df_to_compare[col_name].shape[0]} rows in column {col_name}.\n")
                log_file.write("\n")  # for separating entries
            print(f"Difference detected in the number of rows in column {col_name}")
        else:
            print(f"No difference in the number of rows in column {col_name}")

    @log_function_call
    def _create_new_column_for_classification(self, response_list):
        # TODO: Remove hard-coded values
        if self.eval_column:
            self.df["eval"] = None
        else:
            self.df["category"] = None

        for _, response in response_list:

            lines = [line.strip() for line in response.split("\n") if line.strip()]
            parsed_data = {}

            # Sometimes the output format is [index:value] and sometimes it's [index1, index2:value]
            for line in lines:
                if ':' not in line:
                    # Logging or handling the line without a colon, if needed
                    print(f"Warning: Unexpected format in line '{line}'")
                    continue
                indices, value = line.split(":", 1)

                # If there's a dash, tilde or comma, split accordingly
                separators = ['-', '~', ',']
                for sep in separators:
                    if sep in indices:
                        indices = [int(idx.strip()) for idx in indices.split(sep)]
                        break

                # If indices is still a string (i.e., not a list), it means it's a single index
                if isinstance(indices, str):
                    indices = [int(indices.strip())]
                
                value = value.strip()
                for idx in indices:
                    parsed_data[idx] = value
            
            # Map the values, but retain the original where there's no mapping
            mapped_series = self.df[ExcelFileAnalyzer.INDEX].map(parsed_data)

            if self.eval_column:
                self.df["eval"] = self.df["eval"].combine_first(mapped_series)
            else:
                self.df["category"] = self.df["category"].combine_first(mapped_series)


    
