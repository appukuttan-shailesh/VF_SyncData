# install gspread via: pip install gspread
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from hbp_validation_framework import ModelCatalog

hbp_username = "shailesh"

scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('VF-DataSync-8e2e5296f1c5.json', scope)
gc = gspread.authorize(credentials)

# sc = gc.open("testing_python")
sc = gc.open_by_url("https://docs.google.com/spreadsheets/d/1m3xORxMUf4Nd5nwU6kdcPBs8d4JxOY5jsOoc2E_8Duc/edit#gid=1877135441")

ws = sc.worksheets()
SHEET_NAMES = [x.title for x in ws if not x.title.endswith("_Import")]
SHEET_NAMES.remove("Model overview")
SHEET_NAMES.remove("Example artefact table")
SHEET_NAMES.remove("Dropdown lists")
SHEET_NAMES.remove("CSCS account")

CHECK_COLS = ["Brain Region", "Cell Type", "Species", "Author Organization"]
MC_MAP = {"Brain Region":"brain_region", "Cell Type":"cell_type", "Species":"species", "Author Organization":"organization"}
uniqueVals = {}
for colHead in CHECK_COLS:
    uniqueVals[colHead] = set()

#-------------------------------------------------------------------------------

def getNewVals(sheetName):
    CUR_SHEET = sheetName
    # Selecting a worksheet by title
    worksheet = sc.worksheet(CUR_SHEET)
    # Get all headers
    headers_list = worksheet.row_values(1)

    # check that all the necessary columns are present in the spreadsheet
    for colHead in CHECK_COLS:
        if colHead not in headers_list:
            raise IOError("Worksheet '{}' does not have the required column titled: '{}'".format(CUR_SHEET, colHead))

    # get all data as list of dicts (each row is a dict with key = column heading and value = cell data)
    worksheet_data = worksheet.get_all_records(empty2zero=False, head=1, default_blank='')
    for row in worksheet_data:
        if row["Import to HBP model catalog"] == "yes":
            for colHead in CHECK_COLS:
                uniqueVals[colHead].add(row[colHead].strip())

#-------------------------------------------------------------------------------

for sheet in SHEET_NAMES:
    getNewVals(sheet)

model_catalog = ModelCatalog(hbp_username)
exist_vals = model_catalog.get_attribute_options()
for colHead in CHECK_COLS:
    print ("Current Column: {}".format(colHead))
    all_vals = list(uniqueVals[colHead])
    match_vals = []
    for val in all_vals:
        if val.lower() in map(str.lower, exist_vals[MC_MAP[colHead]]):
            # make neater?
            match_index = map(str.lower, exist_vals[MC_MAP[colHead]]).index(val.lower())
            match_vals.append(exist_vals[MC_MAP[colHead]][match_index])
        else:
            match_vals.append("-")
    with open(colHead+".tsv", 'wb') as myfile:
        myfile.writelines(map("{}\t{}\n".format, all_vals, match_vals))
