import pandas as pd
from pandas import json_normalize
import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import copy
import requests
from datetime import datetime

identifiant = 'd23b2e02-085d-43e5-9e6e-e1d558ebfdd5'
