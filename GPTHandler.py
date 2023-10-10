import json
import os
import openai
import tiktoken
import threading
import inspect
import logging, sys
import SystemMessages

MAX_TOKENS_FOR_CURRENT_MODEL = 1500 # TODO: Add a feature that allows the user to select the model
openai.api_key = os.environ.get('OPENAI_API_KEY')

class GPTHandler:
    
    # class variables
    lock = threading.Lock()
    encoding = tiktoken.get_encoding("cl100k_base")
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    processed_chunks = 0

    @staticmethod
    def clear():
        GPTHandler.processed_chunks = 0

    @staticmethod 
    def get_token_count(content):
        return len(GPTHandler.encoding.encode(content))
    
    @staticmethod
    def get_chunked_tuples(data_structs, gpt_message):
        chunks = []
        current_chunk = ""
        current_token_count = 0

        system_message = gpt_message[0]
        assistant_message = gpt_message[1]

        max_tokens = MAX_TOKENS_FOR_CURRENT_MODEL - GPTHandler.get_token_count(system_message) - GPTHandler.get_token_count(assistant_message)

        # TODO: Add a feature that detects whether current chunk is too large for the model 
        for data_tuple in data_structs:

            if len(data_tuple) == 3:
                idx, target, eval = data_tuple
            elif len(data_tuple) == 2:
                idx, target = data_tuple
                eval = None

            target = str(target).replace('\n', ' ')
            data = str(idx) + ":" + target
            if eval is not None:
                data += ":" + eval + "\n"

            token_count = GPTHandler.get_token_count(data)
            
            if (current_token_count + token_count) > max_tokens:
                # If token limit exceeded, finalize the current chunk and start a new one
                current_chunk = current_chunk[:-1] # Remove the last newline
                chunks.append(current_chunk)
                current_chunk = ""
                current_token_count = 0

            current_chunk += data
            current_token_count += token_count
        
        # Add the last chunk if it has any data
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    @staticmethod
    def __get_response_from_chatgpt(chunk, gpt_message):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SystemMessages.ALL_MESSAGES[gpt_message][0]},
                {"role": "assistant", "content": SystemMessages.ALL_MESSAGES[gpt_message][1]},
                {"role": "user", "content": chunk},
            ],
        ) 
        return response.choices[0].message["content"].strip()

    @staticmethod
    def __threaded_get_response(idx_chunk, num_chunks, chunk, response_list, gpt_message, callback=None):
        try:
            response = GPTHandler.__get_response_from_chatgpt(chunk, gpt_message)
            with GPTHandler.lock:
                response_list.append((idx_chunk, response))
                GPTHandler.processed_chunks += 1
                print(f"{idx_chunk + 1} received: {GPTHandler.processed_chunks}/{num_chunks} completed ({GPTHandler.get_token_count(response)} tokens)")
                if callback:
                    callback(processed_chunks=GPTHandler.processed_chunks)
        except Exception as e:
            print(f"{inspect.currentframe().f_code.co_name}: An error occurred in thread {idx_chunk}: {e}")

    @staticmethod
    def start_threaded_get_response(chunks, gpt_message, callback=None):

        if not chunks:
            print(f"{inspect.currentframe().f_code.co_name}: Please ensure that chunks are created.")
            return

        response_list = []
        threads = []
        num_chunks = len(chunks)

        for idx, chunk in enumerate(chunks):
            response_thread = threading.Thread(target=GPTHandler.__threaded_get_response, 
                                               args=(idx, num_chunks, chunk, response_list, gpt_message, callback),
                                               daemon=True)
            response_thread.start()
            threads.append(response_thread)

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        response_list.sort(key=lambda x: x[0])

        return response_list
    
            