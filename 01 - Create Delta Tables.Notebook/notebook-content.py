# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "7cc0418d-40b3-477a-a237-7cd08a8f9573",
# META       "default_lakehouse_name": "wwilakehouse",
# META       "default_lakehouse_workspace_id": "4c18fd18-0da7-4a76-910a-012419b650c8",
# META       "known_lakehouses": [
# META         {
# META           "id": "7cc0418d-40b3-477a-a237-7cd08a8f9573"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# ### Spark session configuration
# This cell sets Spark session settings to enable _Verti-Parquet_ and _Optimize on Write_. More details about _Verti-Parquet_ and _Optimize on Write_ in tutorial document.

# CELL ********************

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

spark.conf.set("spark.sql.parquet.vorder.enabled", "true")
spark.conf.set("spark.microsoft.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.microsoft.delta.optimizeWrite.binSize", "1073741824")

df = spark.sql("SELECT * FROM wwilakehouse.aggregate_sale_by_date_city LIMIT 1000")
display(df.limit(100))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Fact - Sale
# 
# This cell reads raw data from the _Files_ section of the lakehouse, adds additional columns for different date parts and the same information is being used to create partitioned fact delta table.

# CELL ********************

# Importation des fonctions nécessaires à partir de la bibliothèque PySpark
from pyspark.sql.functions import col, year, month, quarter

# Nom de la table
table_name = 'fact_sale'

# Chargement des données depuis le fichier au format Parquet dans un DataFrame Spark
df = spark.read.format("parquet").load('Files/wwi-raw-data/full/fact_sale_1y_full')

# Ajout de colonnes pour l'année, le trimestre et le mois en utilisant les données de la colonne "InvoiceDateKey"
df = df.withColumn('Year', year(col("InvoiceDateKey")))
df = df.withColumn('Quarter', quarter(col("InvoiceDateKey")))
df = df.withColumn('Month', month(col("InvoiceDateKey")))

# Écriture des données dans un format Delta Lake, avec écrasement des données existantes,
# en partitionnant le DataFrame par année et trimestre, puis enregistrement dans un dossier spécifique
df.write.mode("overwrite").format("delta").partitionBy("Year","Quarter").save("Tables/" + table_name)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Dimensions
# This cell creates a function to read raw data from the _Files_ section of the lakehouse for the table name passed as a parameter. Next, it creates a list of dimension tables. Finally, it has a _for loop_ to loop through the list of tables and call above function with each table name as parameter to read data for that specific table and create delta table.

# CELL ********************

# Importation des types de données nécessaires à partir de la bibliothèque PySpark
from pyspark.sql.types import *

# Fonction pour charger les données complètes à partir de la source
def loadFullDataFromSource(table_name):
    # Chargement des données complètes depuis un fichier au format Parquet dans un DataFrame Spark
    df = spark.read.format("parquet").load('Files/wwi-raw-data/full/' + table_name)
    
    # Suppression de la colonne "Photo" du DataFrame pour des raisons spécifiques
    df = df.drop("Photo")
    
    # Écriture des données dans un format Delta Lake avec écrasement des données existantes,
    # puis enregistrement dans un dossier spécifique correspondant au nom de la table
    df.write.mode("overwrite").format("delta").save("Tables/" + table_name)

# Liste des tables complètes à charger
full_tables = [
    'dimension_city',
    'dimension_date',
    'dimension_employee',
    'dimension_stock_item'
    ]

# Boucle parcourant la liste des tables et appelant la fonction de chargement pour chaque table
for table in full_tables:
    loadFullDataFromSource(table)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
