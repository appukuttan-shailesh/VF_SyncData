# install gspread via: pip install gspread
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from hbp_validation_framework import ModelCatalog

hbp_username = "shailesh"
model_catalog = ModelCatalog(hbp_username, environment="dev")

#-------------------------------------------------------------------------------
valid_vals = model_catalog.get_attribute_options()

# Extend for other sheets
cell_type_map = {
                    "MSN" : "Medium spiny neuron",
                    "MSN D1":"Medium spiny neuron (D1 type)",
                    "MSN D2":"Medium spiny neuron (D2 type)",
                    "FS":"Fast spiking interneuron",
                    "ChIN":"Other",
                    "Network":"Not applicable"
                }
#-------------------------------------------------------------------------------

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

CUR_SHEET = "Basal ganglia_Import_Test"

# Selecting a worksheet by title
worksheet = sc.worksheet(CUR_SHEET)

# Get all headers
headers_list = worksheet.row_values(1)

# check that all the necessary columns are present in the spreadsheet
MAND_COLS = ["Artefact Name", "Entity", "Brain Region", "Cell Type", "Species", "Description", "Artefact Type",
             "Location", "Import to HBP model catalog", "Author", "Author Organization", "Collab ID"]
for colHead in MAND_COLS:
    if colHead not in headers_list:
        raise IOError("Worksheet '{}' does not have the required column titled: '{}'".format(CUR_SHEET, colHead))

# columns that we need to add for import/sync to Model Catalog
MC_COLS = ["model_UUID", "instance_UUIDs", "model_URL" , "Model Catalog URL", "Import Message"]

for colHead in MC_COLS:
    if colHead not in headers_list:
        print ("Adding column: {}".format(colHead))
        worksheet.add_cols(1)
        worksheet.update_cell(1, worksheet.col_count, colHead)

# Get all headers (after above changes)
headers_list = worksheet.row_values(1)

#-------------------------------------------------------------------------------
# `Location` field may have URLs or hyperlinks; we need the latter. These are saved in `model_URL`.

# get all data as list of lists (each row is a list)
worksheet_data = worksheet.get_all_values()

for i in range(1, len(worksheet_data)):
    if worksheet_data[i][headers_list.index("Import to HBP model catalog")] == "yes":
        if not worksheet_data[i][headers_list.index("model_URL")]:
            cell_value = worksheet.cell(i+1, headers_list.index("Location")+1).input_value
            if cell_value.startswith("=HYPERLINK"):
                worksheet.update_cell(i+1, headers_list.index("model_URL")+1, cell_value.split('"')[1])
            elif cell_value.startswith("WholeBrainModel://"):
                worksheet.update_cell(i+1, headers_list.index("model_URL")+1, cell_value.replace("WholeBrainModel://", "/gpfs/bbp.cscs.ch/project/proj15/"))
            else:
                worksheet.update_cell(i+1, headers_list.index("model_URL")+1, cell_value)

#-------------------------------------------------------------------------------
# Add to Model Catalog

# get all data as list of dicts (each row is a dict with key = column heading and value = cell data)
worksheet_data = worksheet.get_all_records(empty2zero=False, head=1, default_blank='')
for idx, row in enumerate(worksheet_data):
    if row["Import to HBP model catalog"] == "yes":
        if row["model_UUID"] or row["instance_UUIDs"]:
            # not handling already imported entries
            print ("Skipped: already imported > {} -> Row: {}".format(CUR_SHEET, idx+2))
            continue
        print "Entity = ", row["Entity"].strip().lower()
        print "Artefact Type = ", row["Artefact Type"].strip().lower()
        if (
                 not (row["Entity"].strip().lower() == "single cell" and  row["Artefact Type"].strip().lower() in ["model", "model fit"])
             and not (row["Entity"].strip().lower() == "network" and  row["Artefact Type"].strip().lower() in ["model", "model fit", "model collection"])
             and not (row["Entity"].strip().lower() in ["subcellular", "intrasignalling"] and  row["Artefact Type"].strip().lower() in ["model", "model fit"])
             and not (row["Entity"].strip().lower() == "molecular" and  row["Artefact Type"].strip().lower() in ["model", "model fit"])
           ):
           # not satisfying guidelines (1)
           print ("Skipped: guidelines failed > {} -> Row: {}".format(CUR_SHEET, idx+2))
           continue
        else:
            if True:
            # try:
                if isinstance(row["Collab ID"], int):
                    model_collab_id = str(row["Collab ID"])
                else:
                    model_collab_id = row["Collab ID"].strip()

                model_name = "IMPORT_" + row["Artefact Name"].strip()

                model_author = row["Author"].strip()

                if "allen" in row["Author Organization"].strip().lower():
                    model_organization = "Allen Institute"
                elif ("bbp" in row["Author Organization"].strip().lower()
                            or "blue brain" in row["Author Organization"].strip().lower()):
                    model_organization = "Blue Brain Project"
                else:
                    model_organization = "HBP-SP6"

                model_private = True

                mtype = [x for x in valid_vals["model_type"] if row["Entity"].strip().lower() == x.lower()]
                if len(mtype) == 1:
                    model_type = mtype[0]
                else:
                    print ("Other model type > {} -> Row: {}".format(CUR_SHEET, idx+2))
                    model_type = "Other"

                # ENHANCE CHECK
                if model_type == "Network":
                    model_cell_type = cell_type_map[model_type]
                else:
                    model_cell_type = cell_type_map[row["Cell Type"].strip()]

                # ENHANCE CHECK
                model_brain_region = row["Brain Region"].strip()

                species = [x for x in valid_vals["species"] if row["Species"].strip().lower() in x.lower()]
                if len(species) == 1:
                    model_species = species[0]
                else:
                    print ("Undefined species > {} -> Row: {}".format(CUR_SHEET, idx+2))
                    model_species = "Undefined"

                model_description = row["Description"].strip()

                instance_version = row["Version"].strip()
                instance_source = row["model_URL"].strip()
                instance_parameters = row["Version parameters (optional)"].strip()
                instance_description = row["Version description"].strip()
                instance_code_format = row["Format"].strip()

                #-------------------------------------------------------------------------------
                # Ensure that there exists a Model Catalog app inside each specified Collab
                # check if apps exist; if not then create them
                model_app_id = model_catalog.exists_in_collab_else_create(model_collab_id)
                model_catalog.set_collab_config(collab_id=model_collab_id, app_id=model_app_id, only_if_new="True")
                #-------------------------------------------------------------------------------

                """
                # Register model without instance
                model = model_catalog.register_model(app_id=model_app_id, name=model_name,
                                author=model_author, organization=model_org,
                                private="False", cell_type=model_cell_type, model_type=model_type,
                                brain_region=model_brain_region, species=model_species,
                                description=model_desc)
                """

                # Register model with instance
                model_uuid = model_catalog.register_model(app_id=str(model_app_id), name=model_name,
                                author=model_author, organization=model_organization,
                                private=model_private, cell_type=model_cell_type, model_type=model_type,
                                brain_region=model_brain_region, species=model_species,
                                description=model_description,
                                instances=[{"source": instance_source,
                                            "version":instance_version, "parameters":instance_parameters,
                                            "description":instance_description,
                                            "code_format":instance_code_format}])

                worksheet.update_cell(idx+2, headers_list.index("model_UUID")+1, model_uuid)
                mc_model_url = "https://collab.humanbrainproject.eu/#/collab/" + \
                                str(model_collab_id) + "/nav/" + str(model_app_id) + "?state=model." + model_uuid
                worksheet.update_cell(idx+2, headers_list.index("Model Catalog URL")+1, mc_model_url)
                worksheet.update_cell(idx+2, headers_list.index("Import Message")+1, "Import Successful!")
            # except Exception as e:
            #     raise Exception("Error: {} for {} -> Row: {}\n".format(e.message, CUR_SHEET, idx+2, e.args))
