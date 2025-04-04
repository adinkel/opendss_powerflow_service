import requests
import time
import pandas as pd
import json

import smartds_importer

BASE_URL = "http://127.0.0.1:8000"


def main():

    circuit = "p10uhs0_1247--p10udt2190"
    s3_path = "https://oedi-data-lake.s3.amazonaws.com/SMART-DS/v1.0/2018/SFO/P10U/scenarios/base_timeseries/opendss/p10uhs0_1247/p10uhs0_1247--p10udt2190/"
    s3_filenames = ['Master.dss', 'Transformers.dss', 'Loads.dss', 'Lines.dss', 'Capacitors.dss', 'LineCodes.dss']

    # Import Circuit Model
    smartds_importer.import_circuit(circuit, s3_path, s3_filenames)

    # Powerflow request
    response = requests.post(f'{BASE_URL}/powerflow/{circuit}', json={"outputs": ["voltage", "current"]})
    task_id = response.json()["task_id"]

    # Wait until complete
    while True:
        status_response = requests.get(f'{BASE_URL}/powerflow/status/{task_id}')
        status_data = status_response.json()
        if status_data.get('status') == 'PENDING':
            time.sleep(2)
        else:
            break

    # Retrieve results
    if status_data.get('status') == 'SUCCESS':  
        result_response = requests.get(f'{BASE_URL}/powerflow/result/{circuit}')
        result_data = result_response.json()

    node_data = []
    for row in result_data['nodes']:
        node_data.append(json.loads(row))

    df = pd.DataFrame(node_data)
    print(df.head())

main()