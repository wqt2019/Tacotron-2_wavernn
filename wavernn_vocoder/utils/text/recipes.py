from utils.files import get_files
from pathlib import Path
from typing import Union
import os


def ljspeech(path: Union[str, Path]):
    csv_file = get_files(path, extension='.csv')

    assert len(csv_file) == 1

    text_dict = {}

    with open(csv_file[0], encoding='utf-8') as f :
        for line in f :
            split = line.split('|')
            text_dict[split[0]] = split[-1]

    return text_dict

def biaobei(path: Union[str, Path],trn_name):
    trn_file = os.path.join(path ,trn_name)

    assert len(trn_file) == 1

    text_dict = {}

    with open(trn_file, encoding='utf-8') as f :
        for line in f :
            split = line.split(',')
            text_dict[split[0]] = split[-1]

    return text_dict



