# install gspread via: pip install gspread
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from hbp_validation_framework import ModelCatalog

hbp_username = "shailesh"

scope = ['https://spreadsheets.google.com/feeds']

credentials = ServiceAccountCredentials.from_json_keyfile_name('VF-DataSync-8e2e5296f1c5.json', scope)

gc = gspread.authorize(credentials)

# sc = gc.open("testing_python")
sc = gc.open_by_url("https://docs.google.com/spreadsheets/d/1gavQH_2JqujQ-7HPhxcFRD_x0BHC9zvCKDWqU1rK-s4/edit#gid=0")

# Selecting a worksheet by title
worksheet = sc.worksheet("Basal ganglia")

# get all data as list of lists (each item is a row)
worksheet_data = worksheet.get_all_values()
# Get all headers
headers_list = worksheet_data[0]

#==============================================================================
 # Add to Model Catalog

model_library = ModelCatalog(hbp_username, environment="dev")

type_col_ind = [i for i,head in enumerate(headers_list) if head.lower() == "artefact type"][0]
for row_entry in worksheet_data[1:]:
    if row_entry[type_col_ind].lower() in ["model", "model collection"]:
        # set model host app ID
        model_app_id = "39968"

        # set model name
        model_name = # TODO

        # set author
        author_col_ind = [i for i,head in enumerate(headers_list) if head.lower() == "author"][0]
        model_author = row_entry[author_col_ind]
        if model_author == "":
            model_author = "Unknown"

        # set organization
        model_org = ""

        # set cell type
        type_col_ind = [i for i,head in enumerate(headers_list) if head.lower() == "cell type"][0]
        model_cell_type = row_entry[type_col_ind]

        # set model type
        if row_entry[type_col_ind].lower() == "model":
            model_type = "Single Cell"
        else:
            model_type = "Network"

        # set model brain region
        region_col_ind = [i for i,head in enumerate(headers_list) if head.lower() == "brain region"][0]
        model_brain_region = row_entry[region_col_ind]

        # set model species
        species_col_ind = [i for i,head in enumerate(headers_list) if head.lower() == "species"][0]
        model_species = row_entry[species_col_ind]

        # set model description
        desc_col_ind = [i for i,head in enumerate(headers_list) if head.lower() == "description"][0]
        model_desc = row_entry[desc_col_ind]

        """
        # Register model without instance
        model = model_catalog.register_model(app_id=model_app_id, name=model_name,
                        author=model_author, organization=model_org,
                        private="False", cell_type=model_cell_type, model_type=model_type,
                        brain_region=model_brain_region, species=model_species,
                        description=model_desc)

        # Register model with instance
        model = model_catalog.register_model(app_id=model_app_id, name=model_name,
                        author=model_author, organization=model_org,
                        private="False", cell_type=model_cell_type, model_type=model_type,
                        brain_region=model_brain_region, species=model_species,
                        description=model_desc,
                        instances=[{"source":"https://www.abcde.com",
                                    "version":"1.0", "parameters":""},
                                   {"source":"https://www.12345.com",
                                    "version":"2.0", "parameters":""}])
        """
