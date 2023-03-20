import pyodbc
from PIL import Image
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import uuid
import datetime
import json
import streamlit.components.v1 as components
from annotated_text import annotated_text
import urllib.request
import json
import os
from azure.cosmos import cosmos_client
from azure.cosmos.partition_key import PartitionKey
import ssl
from io import StringIO


st.set_page_config(
    page_title="Predictive Modelling",
    layout="wide",
    initial_sidebar_state="auto",
)


def add_logo(logo_path, width, height):
    """Read and return a resized logo"""
    logo = Image.open(logo_path)
    modified_logo = logo.resize((width, height))
    return modified_logo


my_logo = add_logo(logo_path="logo.png", width=200, height=100)
st.sidebar.image(my_logo)

with st.sidebar:
    choose = option_menu(
        "Application",
        [
            "Auto Insurance Buy - Existing",
            "Auto Insurance Buy - New",
            "Premium Health Plan - Smart Wearable",
            "Setting"
        ],
        icons=["person-fill", "person-bounding-box", "smartwatch","gear"],
        menu_icon="graph-up-arrow",
        default_index=0,
        styles={
            "container": {
                "padding": "5!important",
                "background-color": "#fafafa",
                "color": "black",
            },
            "icon": {"color": "green", "font-size": "30px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#eee",
                "color": "black",
            },
            "nav-link-selected": {"background-color": "#24292f", "color": "white"},
        },
    )

if choose == "Auto Insurance Buy - Existing":
    st.header("Auto Insurance Buy - Existing")
    st.markdown("<hr>", unsafe_allow_html=True)
    cust_id = st.text_input("Customer ID")

    if st.button("Get Info:"):
        with st.spinner("Customer Deatils Fetching in Progress ..."):
            server = "tcp:slytherin-dev-mssql-server.database.windows.net"
            database = "slytherin-dev-mssqldb"
            username = "sladmin"
            password = "Admin@123"
            port = "1433"
            # ENCRYPT defaults to yes starting in ODBC Driver 18. It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
            cnxn = pyodbc.connect(
                "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
                + server
                + ";DATABASE="
                + database
                + ";ENCRYPT=yes;UID="
                + username
                + ";PWD="
                + password
            )

            data = pd.read_sql(
                f"SELECT  c.customer_name as 'Customer Name', c.phone as 'Customer Phone', c.mail as 'Customer Email', c.sex as 'Customer Gender',a.name as 'Agent Name' FROM dbo.customer c join dbo.agents a on c.agent_id=a.agent_id where c.customer_id = '{cust_id}'",
                cnxn,
            )
            st.success(f"Found the Match for {cust_id}!!!", icon="✅")
            df = pd.read_csv(
                "abfs://raw@slytherinadlsdev.dfs.core.windows.net/auto_insurance/Car_Insurance_CCampaign.csv",
                storage_options={
                    "account_key": "Ow4JwUcFpbQC5tAHpxz4bxeaYtmdxMqY7yRgnOY9X16p8Ef35NwvLagZxfOcDO4xRBvlJIrz2vJU+AStR1nEQw=="
                },
            )
            df = df[df["customer_id"] == str.upper(cust_id)]

        if data.shape[0] >= 1:
            st.markdown(
                "<hr> Customer Detail from Azure SQL Server: </hr>",
                unsafe_allow_html=True,
            )
            st.write(data)

            def allowSelfSignedHttps(allowed):
                # bypass the server certificate verification on client side
                if (
                    allowed
                    and not os.environ.get("PYTHONHTTPSVERIFY", "")
                    and getattr(ssl, "_create_unverified_context", None)
                ):
                    ssl._create_default_https_context = ssl._create_unverified_context

            allowSelfSignedHttps(
                True
            )  # this line is needed if you use self-signed certificate in your scoring service.

            data = {
                "input_data": {
                    "columns": [
                        "customer_id",
                        "birthdate",
                        "GENDER",
                        "RACE",
                        "DRIVING_EXPERIENCE",
                        "EDUCATION",
                        "INCOME",
                        "Vehicle_Age",
                        "Vehicle_Damage",
                        "VEHICLE_OWNERSHIP",
                        "MARRIED",
                        "CHILDREN",
                        "ANNUAL_MILEAGE",
                        "VEHICLE_TYPE",
                        "SPEEDING_VIOLATIONS",
                        "DRIVE_UNDER_INFLUENCE",
                        "PAST_ACCIDENTS",
                        "Vehicle_Damage_1",
                    ],
                    "index": [0],
                    "data": [df.values.tolist()[0][:-1]],
                }
            }

            body = str.encode(json.dumps(data))

            url = "https://slytherin-azure-ml-dev-model.eastus.inference.ml.azure.com/score"
            api_key = "bgmgCwVaSrpW4Yxfpp7Kxrhe5mxk9YOE"
            if not api_key:
                raise Exception("A key should be provided to invoke the endpoint")

            headers = {
                "Content-Type": "application/json",
                "Authorization": ("Bearer " + api_key),
                "azureml-model-deployment": "auto-insurance-logistic-regres",
            }

            req = urllib.request.Request(url, body, headers)

            try:
                response = urllib.request.urlopen(req)

                result = response.read()
                print(result)
            except urllib.error.HTTPError as error:
                print("The request failed with status code: " + str(error.code))

                # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
                print(error.info())
                print(error.read().decode("utf8", "ignore"))
            response = json.loads(result)[0]
            if response == 1:
                annotated_text(("Potential Customer - ML Output: ", "Yes", "#afa"))
            else:
                annotated_text(("Potential Customer - ML Output:", "No", "#faa"))
            existing_response = list(df["Response"])[0]
            if existing_response == 1:
                annotated_text(
                    ("Potential Customer - Campaign Response: ", "Yes", "#afa")
                )
            else:
                annotated_text(
                    ("Potential Customer - Campaign Response:", "No", "#faa")
                )
        else:
            st.warning(f"No Record available for {cust_id}", icon="⚠️")

elif choose == "Premium Health Plan - Smart Wearable":
    st.header("Premium Health Plan - Smart Wearable")
    st.markdown("<hr>", unsafe_allow_html=True)
    cust_id = st.text_input("Customer ID")
    st.write(st.session_state.steps)
    if st.button("Get Info:"):
        with st.spinner("Customer Activity Details Fetching in Progress ..."):
            CONFIG = {
                "ENDPOINT": "https://slytherinnosqldev.documents.azure.com:443/",
                "PRIMARYKEY": "1bAPxdB4MmeqP5WVP8LEoUGlD4Mp4g5B1BR4C65DbjBlmwaEEz1nEAyh0EtE6QvWJyeMnuOm0OqXACDbK3hsQQ==",
                "DATABASE": "slytherincosmosdb",  # Prolly looks more like a name to you
                "CONTAINER": "wearable-logs",  # Prolly looks more like a name to you
            }

            CONTAINER_LINK = f"dbs/{CONFIG['DATABASE']}/colls/{CONFIG['CONTAINER']}"
            FEEDOPTIONS = {}
            FEEDOPTIONS["enableCrossPartitionQuery"] = True
            # There is also a partitionKey Feed Option, but I was unable to figure out how to us it.

            QUERY = {"query": f"SELECT * from c"}

            # Initialize the Cosmos client
            client = cosmos_client.CosmosClient(
                url=CONFIG["ENDPOINT"], credential={"masterKey": CONFIG["PRIMARYKEY"]}
            )
            db = client.create_database_if_not_exists(id=CONFIG["DATABASE"])
            # setup container for this sample
            container = db.create_container_if_not_exists(
                id=CONFIG["CONTAINER"],
                partition_key=PartitionKey(path="/id", kind="Hash"),
            )

            def read_items(container):
                print("\n1.3 - Reading all items in a container\n")

                item_list = list(container.read_all_items(max_item_count=10))
                return item_list

            item_list = read_items(container)

            smart_wearable_data = pd.DataFrame(item_list)
            smart_wearable_data = smart_wearable_data[
                smart_wearable_data["CustomerName"] == str.upper(cust_id)
            ]
            smart_wearable_data["ActivityDate"] = smart_wearable_data[
                "ActivityDate"
            ].str.pad(10, side="left",fillchar ='0')
            
            filtered_data_1 = smart_wearable_data[["ActivityDate", "Calories"]]
            filtered_data_1 = filtered_data_1.rename(
                columns={"ActivityDate": "index"}
            ).set_index("index")
            st.line_chart(filtered_data_1)

            filtered_data_2 = smart_wearable_data[["ActivityDate", "LightActiveDistance",
                                "LoggedActivitiesDistance",
                                "TotalDistance",
                                "TrackerDistance",
                                "VeryActiveDistance"]]
            filtered_data_2 = filtered_data_2.rename(
                columns={"ActivityDate": "index"}
            ).set_index("index")
            st.line_chart(filtered_data_2)

            filtered_data_3 = smart_wearable_data[["ActivityDate", "FairlyActiveMinutes",
                            "LightlyActiveMinutes",
                            "VeryActiveMinutes"]]
            filtered_data_3 = filtered_data_3.rename(
                columns={"ActivityDate": "index"}
            ).set_index("index")
            st.line_chart(filtered_data_3)

            filtered_data_4 = smart_wearable_data[["ActivityDate", "TotalSteps"]]
            filtered_data_4 = filtered_data_4.rename(
                columns={"ActivityDate": "index"}
            ).set_index("index")
            st.line_chart(filtered_data_4)

elif choose == "Auto Insurance Buy - New":
    st.header("Auto Insurance Buy - New")
    st.markdown("<hr>", unsafe_allow_html=True)

    uploaded_files = st.file_uploader("Choose a CSV file", accept_multiple_files=True)
    for uploaded_file in uploaded_files:
        bytes_data = uploaded_file.read()
        s = str(bytes_data, "utf-8")
        data = StringIO(s)
        df = pd.read_csv(data)
        df = df[df.customer_id.notnull()]
        if "Response" in df.columns:
            df = df.drop(["Response"], axis=1)
        st.markdown("<hr> Uploaded Data </hr>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.write(df)

        def allowSelfSignedHttps(allowed):
            # bypass the server certificate verification on client side
            if (
                allowed
                and not os.environ.get("PYTHONHTTPSVERIFY", "")
                and getattr(ssl, "_create_unverified_context", None)
            ):
                ssl._create_default_https_context = ssl._create_unverified_context

        allowSelfSignedHttps(
            True
        )  # this line is needed if you use self-signed certificate in your scoring service.

        data = {
            "input_data": {
                "columns": [
                    "customer_id",
                    "birthdate",
                    "GENDER",
                    "RACE",
                    "DRIVING_EXPERIENCE",
                    "EDUCATION",
                    "INCOME",
                    "Vehicle_Age",
                    "Vehicle_Damage",
                    "VEHICLE_OWNERSHIP",
                    "MARRIED",
                    "CHILDREN",
                    "ANNUAL_MILEAGE",
                    "VEHICLE_TYPE",
                    "SPEEDING_VIOLATIONS",
                    "DRIVE_UNDER_INFLUENCE",
                    "PAST_ACCIDENTS",
                    "Vehicle_Damage_1",
                ],
                "index": list(range(df.shape[0])),
                "data": df.values.tolist(),
            }
        }
        # st.markdown("<hr> Hitting Azure ML API with Auto Insurance Data : </hr>", unsafe_allow_html=True)
        # st.write(data)
        body = str.encode(json.dumps(data))

        url = "https://slytherin-azure-ml-dev-model.eastus.inference.ml.azure.com/score"
        api_key = "bgmgCwVaSrpW4Yxfpp7Kxrhe5mxk9YOE"
        if not api_key:
            raise Exception("A key should be provided to invoke the endpoint")

        headers = {
            "Content-Type": "application/json",
            "Authorization": ("Bearer " + api_key),
            "azureml-model-deployment": "auto-insurance-logistic-regres",
        }

        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req)

            result = response.read()
            print(result)
        except urllib.error.HTTPError as error:
            print("The request failed with status code: " + str(error.code))

            # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
            print(error.info())
            print(error.read().decode("utf8", "ignore"))
        predicted_values = json.loads(result)
        df["Potential Customer"] = predicted_values
        map_dict = {0: "No", 1: "Yes"}
        df["Potential Customer"] = df["Potential Customer"].map(map_dict)
        final_df = df[["customer_id", "Potential Customer"]]

        def color_survived(val):
            color = "green" if val == "Yes" else "red"
            return f"background-color: {color}"

        def color_violation(val):
            color = "white"
            return "color: %s" % color

        st.markdown(
            "<hr> Potential Customer Results from Predictive Model </hr>",
            unsafe_allow_html=True,
        )
        st.markdown("<hr>", unsafe_allow_html=True)
        st.dataframe(
            final_df.style.applymap(
                color_survived, subset=["Potential Customer"]
            ).applymap(color_violation, subset=["Potential Customer"])
        )

        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode("utf-8")

        csv = convert_df(df)

        st.download_button(
            "Download Results",
            csv,
            "potential_auto_insurance_customer.csv",
            "text/csv",
            key="download-csv",
        )
elif choose == "Setting":
    steps = st.text_input("Steps")
    if st.button("Configure"):
        if 'steps' not in st.session_state:
            st.session_state['steps'] = steps
