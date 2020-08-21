#!/usr/bin/env python2
# -*- coding: utf-8 -*-


"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#import json
from sklearn.ensemble import ExtraTreesClassifier
#from sklearn.ensemble import RandomForestClassifier

# endereco da pasta onde estam as amostras em csv     
camCarta = '/run/media/superusuario/Almacen/amostras/mycartas/' 
# endereco da pasta onde seram guardadas as os graficos de importancia
camino = '/home/superusuario/Dados/ProjMapbiomas/collection4/'
filelist = os.listdir(camCarta)
#lsFeatures = []
# ===== diccionario que guardará as bandas de interesse como key 
# =====e como valores a suma da importancia por carta de cada banda

dictImportancia = {}
inicio = False
file = open(camino + "listaFeatNum2.txt", "w")

for myCart in filelist:
    print(myCart)

    dfPtos = pd.read_csv(camCarta + myCart, dtype=None, error_bad_lines=False)
    
    #print(dfPtos.head())
    
    nameFeat = []
    #===== lsFeatExt Bandas de la imagem presentes no csv e que não debem entrar na analises
    lsFeatExt = ['system:index','ano','carta','latitude','longitude','.geo', 'class', 'extreme', 'outlier']
    #==== loop para criar um diccionario com as bandas  de interesse
    for ii in dfPtos.columns:
        if ii not in lsFeatExt:
            #print(ii)
            nameFeat.append(ii)
    # confere que os nomes das bandas estam presentes
    print("lista com nome das bandas", nameFeat) 
    
    # loop paea encher ou nao o diccionario de importancia 
    if inicio == False:
        for ii in nameFeat:
            dictImportancia[ii] = 0.0
        inicio = True
    
       
    
    
    ## == extrair do DataFrame os dados de referencia seram usados no modelo 
    dadosRef = dfPtos['class'][:]
    print(dadosRef[:5])
    
    # == esta operacao e opcional mas ajuda entender o como vc tem distribuida 
    # == as suas amostras
    #===== calcular o histograma da banda de referencia ===
    # === de forma automatica extrai 
    
    print("Construcao do histograma de classes da carta")
    mydict = {}
    for ii in dadosRef:
        if ii not in mydict.keys():
            mydict[ii] = 0
        else:
            valor = mydict[ii]
            mydict[ii] = valor + 1
    
   
    print(mydict)

    # Build a forest and compute the feature importances
    forest = ExtraTreesClassifier(bootstrap=True,
                                  n_estimators=250,
                                  max_leaf_nodes=6,
                                  random_state=0)
    forest.fit(dfPtos[nameFeat], dadosRef)
    
    # == calcula a importancia das features 
    importances = forest.feature_importances_
    #print(importances)
    # dictImportancia , nameFeat
    for ii in range(len(importances)):
        print( 'indice ' + str(ii) + ' importancia ' + str(importances[ii]))        
        vv = dictImportancia[nameFeat[ii]] + importances[ii]
        print(vv)
        dictImportancia[nameFeat[ii]] = vv 
   
    #print(dictImportancia)
    
    # == calcula o desvio padrao das features importante para cada Arvore 
    std = np.std([tree.feature_importances_ for tree in forest.estimators_], axis=0)
    # === ordenar o  pela importancia 
    indices = np.argsort(importances)[::-1]
    print(indices)
    print(type(importances))
    #=================================================================
    #===== salvar a lista das Features mais importante em text========
#    plt.figure(figsize=(30,10))
#    plt.title("Feature importances")
#    plt.bar(range(len(nameFeat)), importances[indices],
#           color="r", yerr=std[indices], align="center")
#    plt.xticks(range(len(nameFeat)), indices)
#    plt.xlim([-1, len(nameFeat)])
#    nomeSave = camino + "plotimportFeat_"+myCart[:-4]+".png"
#    plt.savefig(nomeSave, dpi=70, facecolor='w', edgecolor='w',
#            orientation='portrait', papertype=None, format='png',
#            transparent=False, bbox_inches=None, pad_inches=0.1,
#            frameon=None, metadata=None)
    plt.show()
    #Print of name Feature
print("aqui lista de importnacia")
for mkeys, valor in dictImportancia.items():
    print(mkeys + ' : ' + str(valor))

importances = [] 
for ii in dictImportancia.values():
    print(ii)
    importances.append(ii)
#importances = np.array(dictImportancia.values())
indices = np.argsort(importances)[::-1]
myNameFeatImp = []
myFeatimportante= []
for ii in indices:
    myFeatimportante.append(importances[ii])
    myNameFeatImp.append(nameFeat[ii])


df = pd.DataFrame(list(zip(myFeatimportante,myNameFeatImp))).set_index(1) # indices,
df.to_csv(camino + 'tabelaImportanciasFeaturesExtraTree.csv', header= ['importancia'], sep= ';')
nomeSave = camino+"plotimportFeat_All_CartasExtraTree.png"
ax = df.plot.bar(figsize=(30,10), title= 'Importancia das Caracteristicas', color='r')
ax.legend(loc=0, labels= ['soma da importancia X Carta'])  #
ax.set_xlabel("Lista de Features")
ax.set_ylabel("indice importancia")
fig = ax.get_figure()
fig.savefig(nomeSave, dpi=70, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format='png',
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)

