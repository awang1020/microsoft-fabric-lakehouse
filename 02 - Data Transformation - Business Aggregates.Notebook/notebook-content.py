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

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### Approach #1 - sale_by_date_city
# In this cell, you are creating three different Spark dataframes, each referencing an existing delta table.

# CELL ********************

df_fact_sale = spark.read.table("wwilakehouse.fact_sale") 
df_dimension_date = spark.read.table("wwilakehouse.dimension_date")
df_dimension_city = spark.read.table("wwilakehouse.dimension_city")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# In this cell, you are joining these tables using the dataframes created earlier, doing group by to generate aggregation, renaming few of the columns and finally writing it as delta table in the _Tables_ section of the lakehouse.

# CELL ********************

sale_by_date_city = df_fact_sale.alias("sale") \
.join(df_dimension_date.alias("date"), df_fact_sale.InvoiceDateKey == df_dimension_date.Date, "inner") \
.join(df_dimension_city.alias("city"), df_fact_sale.CityKey == df_dimension_city.CityKey, "inner") \
.select("date.Date", "date.CalendarMonthLabel", "date.Day", "date.ShortMonth", "date.CalendarYear", "city.City", "city.StateProvince", "city.SalesTerritory", "sale.TotalExcludingTax", "sale.TaxAmount", "sale.TotalIncludingTax", "sale.Profit")\
.groupBy("date.Date", "date.CalendarMonthLabel", "date.Day", "date.ShortMonth", "date.CalendarYear", "city.City", "city.StateProvince", "city.SalesTerritory")\
.sum("sale.TotalExcludingTax", "sale.TaxAmount", "sale.TotalIncludingTax", "sale.Profit")\
.withColumnRenamed("sum(TotalExcludingTax)", "SumOfTotalExcludingTax")\
.withColumnRenamed("sum(TaxAmount)", "SumOfTaxAmount")\
.withColumnRenamed("sum(TotalIncludingTax)", "SumOfTotalIncludingTax")\
.withColumnRenamed("sum(Profit)", "SumOfProfit")\
.orderBy("date.Date", "city.StateProvince", "city.City")

sale_by_date_city.write.mode("overwrite").format("delta").option("overwriteSchema", "true").save("Tables/aggregate_sale_by_date_city")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### Approach #2 - sale_by_date_employee
# In this cell, you are creating a temporary Spark view by joining 3 tables, doing group by to generate aggregation, renaming few of the columns. 

# CELL ********************

# MAGIC %%sql
# MAGIC -- Cette ligne crée une vue temporaire nommée "sale_by_date_employee" ou la remplace si elle existe déjà.-- 
# MAGIC CREATE OR REPLACE TEMPORARY VIEW sale_by_date_employee
# MAGIC AS
# MAGIC SELECT
# MAGIC 	DD.Date, DD.CalendarMonthLabel
# MAGIC     , DD.Day, DD.ShortMonth Month, CalendarYear Year
# MAGIC 	,DE.PreferredName, DE.Employee
# MAGIC 	,SUM(FS.TotalExcludingTax) SumOfTotalExcludingTax
# MAGIC 	,SUM(FS.TaxAmount) SumOfTaxAmount
# MAGIC 	,SUM(FS.TotalIncludingTax) SumOfTotalIncludingTax
# MAGIC 	,SUM(Profit) SumOfProfit 
# MAGIC FROM wwilakehouse.fact_sale FS
# MAGIC INNER JOIN wwilakehouse.dimension_date DD ON FS.InvoiceDateKey = DD.Date
# MAGIC INNER JOIN wwilakehouse.dimension_Employee DE ON FS.SalespersonKey = DE.EmployeeKey
# MAGIC GROUP BY DD.Date, DD.CalendarMonthLabel, DD.Day, DD.ShortMonth, DD.CalendarYear, DE.PreferredName, DE.Employee
# MAGIC ORDER BY DD.Date ASC, DE.PreferredName ASC, DE.Employee ASC

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# In this cell, you are reading from the temporary Spark view created in the previous cell and and finally writing it as delta table in the _Tables_ section of the lakehouse.

# CELL ********************

# Sélectionne toutes les colonnes de la vue temporaires
sale_by_date_employee = spark.sql("SELECT * FROM sale_by_date_employee")

#Enregistre le contenu du df dans un format delta Lake
sale_by_date_employee.write.mode("overwrite").format("delta").option("overwriteSchema", "true").save("Tables/aggregate_sale_by_date_employee")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.sql("SELECT * FROM wwilakehouse.dimension_customer LIMIT 1000")
display(df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from powerbiclient import QuickVisualize, get_dataset_config, Report

PBI_visualize = QuickVisualize(get_dataset_config(df))
PBI_visualize

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
