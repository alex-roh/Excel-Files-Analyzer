import tkinter
import tkinter.ttk
import SystemMessages
from tkinter import StringVar, filedialog, messagebox
from ExcelFileAnalyzer import ExcelFileAnalyzer

class ExcelAnalyzerApp:

    # Constants
    TITLE = "Excel Analyzer"
    FILE_TYPES = [("Excel files", "*.xlsx *.xls")]
    DEFAULT_LANGUAGE = "Korean"
    DEFAULT_COLUMN = "opinion"

    # Singleton
    _instance = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = ExcelAnalyzerApp()
        return cls._instance

    def __init__(self):

        # Singleton
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        # Init window
        self.app = tkinter.Tk()
        self.app.title(self.TITLE)
        
        # Init variables
        self.num_chunks = 0
        self.processed_chunks = 0
        self.target_column = StringVar(value=self.DEFAULT_COLUMN)

        # Set up the ExcelFileAnalyzer
        self.excel_file_analyzer = ExcelFileAnalyzer()
        self.excel_file_analyzer.attach(self)

        # Init UI components
        self.init_ui()
        self.__initialized = True

    def init_ui(self):
        frame = tkinter.Frame(master=self.app)
        frame.pack()
        self.init_ui_components(frame)

    def init_ui_components(self, frame):

        # Classify an excel file (GPT-powered)

        self.open_excel_file_button, self.excel_file_label = self._init_button_label_component_pack(
            frame, "Open Target Excel File", lambda: self.excel_file_analyzer.open_excel_file(), "No file selected")
        
        self.col_combobox = tkinter.ttk.Combobox(frame, textvariable=self.target_column, state="disabled")
        self.col_combobox.pack()

        self.message_combobox = tkinter.ttk.Combobox(frame, state="readonly")
        self.message_combobox.configure(values=list(SystemMessages.ALL_MESSAGES.keys()))
        self.message_combobox.set(next(iter(SystemMessages.ALL_MESSAGES.keys())))
        self.message_combobox.pack()

        self.gpt_classification_button, self.gpt_classification_label = self._init_button_label_component_pack(
            frame, "Run GPT-powered Classification", lambda: self.excel_file_analyzer.message_resolver(
                self.target_column.get(), self.message_combobox.get()), "Not processed yet") #TODO: show the progress
        
        self.save_label = tkinter.Label(frame, text="Not saved yet", wraplength=350)
        self.save_label.pack()

        self.clear_classification_button = tkinter.Button(frame, text="Clear", command=lambda: self.excel_file_analyzer.clear_classify())
        self.clear_classification_button.pack()

        # Concatenate excel files

        self.seperator_1 = tkinter.ttk.Separator(frame, orient="horizontal")
        self.seperator_1.pack(fill="x", pady=10)

        self.concat_excel_file_button, self.concat_excel_file_label = self._init_button_label_component_pack(
            frame, "Concatenate Excel Files", lambda: self.excel_file_analyzer.concatenate_excel_files(), "No file selected")
        
        self.seperator_2 = tkinter.ttk.Separator(frame, orient="horizontal")
        self.seperator_2.pack(fill="x", pady=10)

        # Combine two excel files

        combine_excel_frame = tkinter.Frame(frame)
        combine_excel_frame.pack(pady=0)

        self.combine_excel_file_label = tkinter.Label(combine_excel_frame, text="Combine Two Excel Files", wraplength=350)
        self.combine_excel_file_label.grid(row=0, column=0, columnspan=2, pady=5)

        self.combine_excel_file_button1, self.combine_0_excel_label = self._init_button_label_component_grid(
            combine_excel_frame, "Base File", lambda: self.excel_file_analyzer.combine_two_excel_files(mode='open file', num=0), "No file",
            row=1, column=0)
        
        self.combine_excel_file_button2, self.combine_1_excel_label = self._init_button_label_component_grid(
            combine_excel_frame, "Extra File", lambda: self.excel_file_analyzer.combine_two_excel_files(mode='open file', num=1), "No file",
            row=1, column=1)
        
        self.combine_excel_file_button3 = tkinter.Button(combine_excel_frame, text="Combine", command=lambda: self.excel_file_analyzer.combine_two_excel_files())
        self.combine_excel_file_button3.grid(row=3, column=0, columnspan=2, pady=5)

        self.clear_combine_button = tkinter.Button(frame, text="Clear", command=lambda: self.excel_file_analyzer.clear_combine())
        self.clear_combine_button.pack(pady=5)

            
    def run(self):
        self.update_periodically()
        self.app.mainloop()
    
    def update(self, event, **kwargs):
        update_mapping = {
            "request_excel_file": lambda **kwargs: self._update_file("Open Excel File", **kwargs),
            "request_mutiple_excel_files": lambda **kwargs: self._update_files("Open Excel Files to Concatenate", **kwargs),

            "set_column_names": lambda **kwargs: self._set_column_names(kwargs.get("column_names")),

            "update_content_label": lambda **kwargs: self._set_label_text(self.excel_file_label, kwargs.get("file_name")),
            "update_gpt_classification_label": lambda **kwargs: self._set_label_text(self.gpt_classification_label, kwargs.get("message")),
            "update_save_label": lambda **kwargs: self._set_label_text(self.save_label, kwargs.get("message")),
            "update_concat_excel_label": lambda **kwargs: self._set_label_text(self.concat_excel_file_label, kwargs.get("file_name")),
            "update_combine_0_excel_label": lambda **kwargs: self._set_label_text(self.combine_0_excel_label, kwargs.get("file_name")),
            "update_combine_1_excel_label": lambda **kwargs: self._set_label_text(self.combine_1_excel_label, kwargs.get("file_name")),
            
            "set_num_chunks": lambda **kwargs: self._set_num_chunks(kwargs.get('num_chunks')),
            "set_processed_chunks": lambda **kwargs: self._set_processed_chunks(kwargs.get('processed_chunks')),
            
            "show_error": lambda **kwargs: self._show_error(kwargs.get("message")),
        }
        return update_mapping.get(event, lambda **kwargs: None)(**kwargs)
    
    def update_periodically(self):
        if self.processed_chunks == self.num_chunks == 0:
            self._set_label_text(self.gpt_classification_label, f"Waiting for the chunks to be processed...")
        elif self.num_chunks > 0 and self.processed_chunks == 0:
            self._set_label_text(self.gpt_classification_label, f"Sending {self.num_chunks} chunks to GPT-3.5 Turbo...")
        elif self.processed_chunks > 0:
            self._set_label_text(self.gpt_classification_label, f"Finished {self.processed_chunks} chunks out of {self.num_chunks} chunks")
        elif self.processed_chunks == self.num_chunks:
            self._set_label_text(self.gpt_classification_label, f"Completed the classification!")

        # Periodic update (100ms)
        self.app.after(100, self.update_periodically)
        
    # Private methods
    def _set_column_names(self, column_names):
        if column_names:
            self.column_names = column_names
            self.col_combobox.configure(state="readonly")
            self.col_combobox.configure(values=self.column_names)

    def _update_file(self, title, **kwargs):
        return filedialog.askopenfilename(title=title, filetypes=self.FILE_TYPES)
    
    def _update_files(self, title, **kwargs):
        return filedialog.askopenfilenames(title=title, filetypes=self.FILE_TYPES)

    def _set_label_text(self, label, text):
        label.configure(text=text)

    def _set_num_chunks(self, num_chunks):
        self.num_chunks = num_chunks

    def _set_processed_chunks(self, processed_chunks):
        self.processed_chunks = processed_chunks

    def _show_error(self, message):
        messagebox.showerror("Error", message)

    def _init_button_label_component_pack(self, frame, button_text, button_command, label_text):
        button = tkinter.Button(frame, text=button_text, command=button_command)
        label = tkinter.Label(frame, text=label_text, wraplength=350)
        button.pack()
        label.pack()
        return button, label
    
    def _init_button_label_component_grid(self, frame, button_text, button_command, label_text, row, column, columnspan=1):
        button = tkinter.Button(frame, text=button_text, command=button_command)
        label = tkinter.Label(frame, text=label_text, wraplength=350)
        button.grid(row=row, column=column, columnspan=columnspan)
        label.grid(row=row+1, column=column, columnspan=columnspan)
        return button, label

if __name__ == "__main__":
    app = ExcelAnalyzerApp()
    app.run()

