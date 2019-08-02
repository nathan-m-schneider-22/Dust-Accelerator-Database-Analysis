echo off

echo Beginning Setup Procedure
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12;
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install mysql-connector-python
python -m pip install -U matplotlib

echo done
python .\generate_sessions.py
type .\example_input.txt | python .\rate_results.py

Echo Setup Complete 