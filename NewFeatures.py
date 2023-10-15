import os
from tkinter import filedialog
import pandas as pd
from konlpy.tag import Okt
import seaborn as sns

FILE_TYPES = [("Excel files", "*.xlsx *.xls")]

def extract_nouns(opinion):
    return okt.nouns(str(opinion))

def most_frequent(noun_list):
    return max(set(noun_list), key = noun_list.count) if noun_list else None

okt = Okt()
target_file = filedialog.askopenfilename(filetypes=FILE_TYPES)
file_name = os.path.basename(target_file)
df = pd.read_excel(target_file, engine='openpyxl')

df = df[df['eval'].notna()]
df['nouns'] = df['eval'].apply(extract_nouns)

df['frequent_noun'] = df['nouns'].apply(most_frequent)
summary = df['frequent_noun'].value_counts()
sns.barplot(x=summary.index, y=summary.values)

df.to_excel(f"Converted_{file_name}", index=False, engine='openpyxl')