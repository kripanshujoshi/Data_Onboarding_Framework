import pandas as pd
import pytest
from modules.metadata import extract_metadata_from_dataframe


def test_empty_dataframe():
    df = pd.DataFrame()
    result = extract_metadata_from_dataframe(df, 'src', 'table.csv')
    assert result.empty


def test_numeric_and_string_columns():
    data = {'num_col': ['1', '2', '3'], 'str_col': ['a', 'b', 'c']}
    df = pd.DataFrame(data)
    result = extract_metadata_from_dataframe(df, 'src', 'table.csv')
    assert set(result['field_nm']) == {'num_col', 'str_col'}
    # numeric column detected as NUMBER
    num_type = result.loc[result['field_nm']=='num_col', 'datatype_nm'].iloc[0]
    assert 'NUMBER' in num_type
    # string column detected as VARCHAR
    str_type = result.loc[result['field_nm']=='str_col', 'datatype_nm'].iloc[0]
    assert 'VARCHAR' in str_type


def test_primary_key_detection():
    # distinct values in column -> primary key flagged
    df = pd.DataFrame({'id': ['1','2','3'], 'val': ['x','x','y']})
    result = extract_metadata_from_dataframe(df, 'src', 'table.csv')
    pk = result.loc[result['field_nm']=='id', 'key_ind'].iloc[0]
    assert pk == 'X'
