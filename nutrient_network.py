import pandas as pd
import numpy as np
import networkx as nx
import community
import os, os.path

#Used to format data before turning into a DataFrame
def strip(text):
    try:
        return float(text.strip("~"))
    except:
        return text.strip("~")

#Turn two files into dataframes
with open ("NUT_DATA.txt") as infile:
    nut_data = pd.read_csv(infile, sep="^", usecols=[0,1,2], names=("NBD_No", "Nutr_No", "Nutr_Val"), converters = {'NBD_No' : strip,'Nutr_No' : strip,'Nutr_Val' : strip})

#Set any nutrition value to 1, remove anything less than or equal to zero
nut_data['Nutr_Val'][nut_data['Nutr_Val'] > 0] = 1
nut_data = nut_data[nut_data['Nutr_Val'] > 0]

with open ("NUTR_DEF.txt") as infile:
    nutr_def = pd.read_csv(infile, sep="^", usecols=[0,3], names=("Nutr_No", "NutrDesc"), index_col=(0), converters = {'Nutr_No' : strip, 'NutrDesc' : strip})

#Find correlation of data, remove self-correlations, snip values.
corrdata = nut_data.pivot(index='NBD_No', columns='Nutr_No').fillna(0).corr()

corrdata -= np.eye(len(corrdata))

# We consider two nutrients to be similar if their correlation exceeds 0.5.
corrdata = corrdata[corrdata >= 0.5].fillna(0)

#Build and label network from data.
nut_network = nx.from_numpy_matrix(corrdata.values)

labels = dict(enumerate(corrdata.columns))
for key in labels:
      labels[key] = labels[key][1]

nx.relabel_nodes(nut_network, labels, copy=False)

nx.relabel_nodes(nut_network, nutr_def.to_dict()['NutrDesc'], copy=False)

#Finds modularity of best partitions, describes clusters.
partition = community.best_partition(nut_network)
print("Modularity:", community.modularity(partition, nut_network))

HOW_MANY = 10
def describe_cluster (x):
    # x is a frame; select the matching rows from "domain"
    rows = nut_data.ix[x.index]
    # Calculate row sums, sort them, get the last HOW_MANY
    top_N = rows.sum(axis=1).sort_values(ascending=False)[ : HOW_MANY]
    # What labels do they have?
    return top_N.index.values

word_clusters = pd.DataFrame({"part_id" : pd.Series(partition)})
results = word_clusters.groupby("part_id").apply(describe_cluster)
_ = [print("--", "; ".join(r.tolist())) for r in results]

#Saves to file.
if not os.path.isdir("results"):
    os.mkdir("results")
with open("results/nut_data.graphml", "wb") as ofile:
    nx.write_graphml(nut_network, ofile)
