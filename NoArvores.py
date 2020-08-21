#!/home/superusuario/py-env/py3IA/lib/python3.7
# -*- coding: utf-8 -*-

"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from collections import OrderedDict

from sklearn.ensemble import RandomForestClassifier


camino = '/run/media/superusuario/Almacen/amostras/Cartas/'
caminoOut = '/home/superusuario/Dados/ProjMapbiomas/collection4/graficos'


filelist = os.listdir(camino)
#print(filelist)

for myCart in filelist:
    print(myCart)
    
    dfPtos = pd.read_csv(camino + myCart, dtype=None, error_bad_lines=False)
    
    print("tamano inicial", dfPtos.shape)
    dfPtos = dfPtos[dfPtos['ano'] == 2017]
    print(dfPtos['ano'][:5])

    print("tamano final", dfPtos.shape)
    nameFeat = {}
    print("Bandas da imagen")
    
    lsFeatExt = ['system:index','ano','carta','latitude','longitude','.geo', 'class']
    cont = 0
    for ii in dfPtos.columns:
        if ii not in lsFeatExt:
            #print(ii)
            nameFeat[ii] = cont
            cont += 1

    bandaRef = ['class']
    dadosRef = dfPtos[bandaRef][:]
    print(dadosRef[:5])
#    
#    print(dfPtos[nameFeat.keys()][:5])
#    print(dfPtos['ano'][:5])

    #===== calcular o histograma da banda de referencia ===
    print("classes presentes na carta")
    valor = []
    for ii in dadosRef['class']:
        if ii not in valor:
            valor.append(ii)
    print(valor)
    mydict = {}
    for ii in valor:
        mydict[ii] = 0
    #print(mydict)
    for u in dadosRef['class']:
        vv = mydict[u]
        mydict[u] = vv + 1
    
    print("mi propio histograma ")
    print(mydict)

    # Build a forest and compute the feature importances
    forest = RandomForestClassifier(bootstrap=True,
                                  n_estimators=5,
                                  max_depth = 4,
                                  max_features= 8,
                                  warm_start=False,
                                  max_leaf_nodes=6,
                                  oob_score=True
                                  )

    min_estimators = 10
    max_estimators = 130
    noArvls = range(min_estimators, max_estimators, 5)
    mFeat = range(4,10)
    
    # Map a classifier name to a list of (<n_estimators>, <error rate>) pairs.
    error_rate = OrderedDict(('RandomForestClassifier, max_features='+str(xx), []) for xx in mFeat)
    dict_error_rate = {}
    for ii in error_rate:
        print(ii)
        dict_error_rate[ii] = []
    
    print(dict_error_rate)
    
    for lnf in error_rate:    
        nf = int(lnf[-1])
        print("labe: ", lnf)
        for noA in noArvls:
            forest.set_params(max_features = nf)
            forest.set_params(n_estimators = noA)
            print("classificando !")
            forest.fit(dfPtos[nameFeat], dadosRef['class'])
             # Record the OOB error for each `n_estimators=i` setting.
            oob_error = 1 - forest.oob_score_
            tuplass = (noA, oob_error)
            print("erro da classification", tuplass)
            dict_error_rate[lnf].append(tuplass)
    
    print("Generate the OOB error rate")
    # Generate the "OOB error rate" vs. "n_estimators" plot.
    for label, clf_err in dict_error_rate.items():
        xs, ys = zip(*clf_err)
        plt.plot(figsize=(60,20))
        plt.plot(xs, ys, label=label)
        plt.legend(loc="upper right")
            
    nomeSave = caminoOut+"plotiNoArv_" + myCart +".png"
    plt.savefig(nomeSave, dpi=70, facecolor='w', edgecolor='w',
            orientation='portrait', papertype=None, format='png',
            transparent=False, bbox_inches=None, pad_inches=0.1,
            frameon=None, metadata=None)       
    plt.xlim(min_estimators, max_estimators)
    plt.xlabel("n_estimators")
    plt.ylabel("OOB error rate")
    plt.title(myCart)
    plt.show()
   
