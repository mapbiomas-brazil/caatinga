import numpy as np
import os
import pandas as pd
from imblearn.over_sampling import SMOTE, RandomOverSampler
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline
from collections import Counter
import json 

# def exportarPointToAssets (featCol, name, geometria):

#     assetId = 'users/mapbiomascaatinga04/projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/RoisSmoteBacias/'

#     paramExp = {
#         'image': featCol, 
#         'description': name, 
#         'assetId': assetId + name
#     }

#     tarefa = ee.batch.Export.table.toAsset(**paramExp)
#     tarefa.start()
#     tarefa.status()

#     print("exportando imagem : {}".format(name))

#'743','755','772','775','7614',
nameBacias = [
    '743','755','772','775','7614'
]
# nameBacias = [
#       '732','741','742','743','744', '745','746','747','751','752',
#       '753', '754','755','756','757','758','759','762','763','765',
#       '766','767','771','772','773', '774', '775','776','777',
#       '7611','7612','7613','7614','7615','7616', '7617','7618','7619'
# ]


pd.set_option("display.precision", 8)

PATH = "./newROIs/ROIsClusterC1/"
PathOutPut = "./newROIs/OUTPUT/"
# for roi_file in os.listdir(PATH):

for bacia in nameBacias:
    print("analisando bacia ### {} ###".format(bacia))

    dfROIs = None
    lsDF = []

    roi_file = 'RF_BACIA_' + bacia + '_.csv'

    df_roiGeral = pd.read_csv(PATH + roi_file)

    for year in range(1985, 2019):
        print("analisando ano == {} ==".format(year))

        df_roi = df_roiGeral[df_roiGeral['year'] == year].copy()
        
        y = df_roi["class"]
        X = df_roi.drop(["class"], axis=1)
        
        print("tamanho inicial da tabela ", X.shape)
        print(y.shape)
        # print(X.isnull().any())
        counter = Counter(y)
        # print("Frecuencia das classes ", counter)

        counter = dict(counter)
        print("Frecuencia das classes: \n", counter) 
        # maximun = max(list(counter.values()))
        # print(maximun)

        minimun = min(list(counter.values()))
        
        # Fazer os dados númericos para o smote funcionar
        X = X.drop(["system:index"], axis=1)
        
        # X[".geo"] = X[".geo"].apply(lambda x: json.loads(x))
        
        # #extracting values from dict .geo
        # df = pd.io.json.json_normalize(X[".geo"])
        # df2 = df["coordinates"].apply(lambda x: pd.Series(x, dtype=np.float32))
        # df2 = df2.rename(columns= {0: 'lat', 1:'lon'})
        
        X = X.drop([".geo"], axis=1)
        # X["lat"] = df2['lat'].round(decimals=6 )
        # X['lon'] = df2["lon"].round(decimals=6 )

        if minimun > 25:
            print("normal smote")
            pipeline = SMOTE()
            X, y = pipeline.fit_resample(X, y)
        
        else:
            print("hibrid smote")
            over = SMOTE()
            random = RandomOverSampler(sampling_strategy= 'minority')
            steps = [('r', random), ('o', over)]
            pipeline = Pipeline(steps=steps)
            X, y = pipeline.fit_resample(X, y)

        counter = Counter(y)
        print("Frecuencia das classes SMOTE \n", counter)
        # print(X.columns)

        X['class'] = y        
        # print(X.columns)
        
        lsDF.append(X.copy())
        
    dfROIs = pd.concat(lsDF)
    dfROIs['system:index'] = dfROIs.index
    nameFile = 'RF_BACIA_' + bacia + '.csv'
    dfROIs.to_csv(PathOutPut + nameFile)


        # # define pipeline
        # over = SMOTE(sampling_strategy=counter)
        # under = RandomUnderSampler(sampling_strategy=0.5)
        # steps = [('o', over), ('u', under)]
        # pipeline = Pipeline(steps=steps)
        # # transform the dataset
        # X, y = pipeline.fit_resample(X, y)
        # # summarize the new class distribution
        # counter = Counter(y)
        # print(counter)