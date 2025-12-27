import pandas as pd
from csv_data_quality_checker import check_missing_values

def test_no_missing():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    issues = check_missing_values(df)
    assert len(issues) == 0, "Should detect zero missing"
