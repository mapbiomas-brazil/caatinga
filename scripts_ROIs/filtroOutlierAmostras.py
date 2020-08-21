#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
# cluster [WEKA CobWb ] == > https://link.springer.com/content/pdf/10.1007/BF00114265.pdf
'''

import ee 
import gee
import json
import csv
import sys
import random 
import arqParametros as arqParam

try:
  ee.Initialize()
  print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
  print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
sys.setrecursionlimit(1000000000)



params = {
    'assetBacia': 'users/diegocosta/baciasRecticadaCaatinga',
    'assetROIs': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/ROIsXBaciasBalv2'},
    'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/ROIsXBaciasBalClusterv2/',
    'pmtClustLVQ': { 'numClusters': 6, 'learningRate': 0.0001, 'epochs': 800},
    'splitRois': 0.8,
     'numeroTask': 6,
    'numeroLimit': 40,
    'conta' : {
        '0': 'caatinga01',
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',        
        '25': 'solkan1201',
        '27': 'diegoGmail',
        '30': 'rodrigo',
        '34': 'Rafael'        
    },
}


list_anos = [k for k in range(1985,2019)]
# print('lista de anos', list_anos)
lsNamesBacias = arqParam.listaNameBacias
lsBacias = ee.FeatureCollection(params['assetBacia'])

bandNames = [
    'median_gcvi_dry','median_gcvi_wet','median_gvs','median_gvs_dry','median_gvs_wet',
    'median_nir_dry','median_nir_wet','median_savi_dry','median_savi_wet', 'median_ndwi_wet', 
    'median_evi2', 'median_fns_dry','median_ndwi_dry','median_evi2_dry','median_ndwi'
]

#=====================================#
# gerenciador de contas para controlar# 
# processos task no gee               #
#=====================================#
def gerenciador(cont, param):    
    
    numberofChange = [kk for kk in param['conta'].keys()]

    if str(cont) in numberofChange:
        
        gee.switch_user(param['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
    elif cont > param['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont

#salva ftcol para um assetindexIni
def saveToAsset(collection, name):    
    
    optExp = {
            'collection': collection, 
            'description': name, 
            'assetId': params['outAsset'] + name           
    }
    
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    
    print("exportando ROIs da bacia $s ...!", name)

def GetPolygonsfromFolder(NameBacias):
    
    getlistPtos = ee.data.getList(params['assetROIs'])

    ColectionPtos = ee.FeatureCollection([])
    
    for idAsset in getlistPtos: 
        
        path_ = idAsset.get('id')
        # print(path_) 
        
        lsFile =  path_.split("/")
        name = lsFile[-1]
        newName = name.split('_')

        if newName[0] == NameBacias:

            print(path_)

            FeatTemp = ee.FeatureCollection(path_)
    
            ColectionPtos = ColectionPtos.merge(FeatTemp)

    ColectionPtos = ee.FeatureCollection(ColectionPtos)
        
    return  ColectionPtos


def selectClassClusterAgrupado (dictFeat):

    keyC = 0
    maxC = 0

    for kk, vv in dictFeat.items():

        if vv > maxC:
            maxC = vv
            keyC = kk

    print("O <- {} -> é o Cluster com maior numero de pontos ".format(keyC))

    return keyC

arqFeitos = open("lsBaciasROIsfeitasBalanCluster2.txt", 'r')

baciasFeitas = [] 

for ii in arqFeitos.readlines():    
    ii = ii[:-1]
    # print(" => " + str(ii))
    baciasFeitas.append(ii)


arqFeitos = open("lsBaciasROIsfeitasBalanCluster2.txt", 'a+')

arqRelatorio = open("Relatorio Cluster Outlier2.txt", 'a+')

for nbacias in lsNamesBacias:

    if nbacias not in baciasFeitas:

        texto = " procesando a bacia " + nbacias
        print(texto)
        arqRelatorio.write(texto + '\n')

        colecaoPontos = ee.FeatureCollection([])

        ROIsTemp = GetPolygonsfromFolder(nbacias)

        for _ano in list_anos:

            texto = "ano: " + str(_ano)
            print(texto)
            arqRelatorio.write(texto + '\n')

            ROIsTempA = ROIsTemp.filter(ee.Filter.eq('year', _ano))

            ROIsTempA = ROIsTempA.randomColumn('random')    
            trainingROI = ROIsTempA.filter(ee.Filter.lt('random', params['splitRois']))

            histo = trainingROI.aggregate_histogram('class').getInfo()
            texto = " Histograma para treinar {} ".format(histo)
            print(texto) 
            arqRelatorio.write(texto + '\n')
            classROIs = [k for k in histo.keys()] 

            params['pmtClustLVQ']['numClusters'] = len(classROIs)
            
            CLVQ = ee.Clusterer.wekaLVQ(**params['pmtClustLVQ']).train(trainingROI.select(bandNames), bandNames)
            newROIsTempA = ROIsTempA.cluster(CLVQ, 'newclass')

            texto = "iterando por classes"
            print(texto) 
            arqRelatorio.write(texto + '\n')

            for cc in classROIs:
                
                itemClassRoi = newROIsTempA.filter(ee.Filter.eq("class", int(cc)))

                histoTemp = itemClassRoi.aggregate_histogram('newclass').getInfo()

                texto = "histograma cluster da classe " + str(cc)
                print(texto)
                arqRelatorio.write(texto + '\n')
                texto = "{}".format(histoTemp)
                print(texto)
                arqRelatorio.write(texto + '\n')

                selectCC = selectClassClusterAgrupado(histoTemp)

                trainingROI = None
                trainingROI = itemClassRoi.filter(ee.Filter.eq('newclass', int(selectCC)))

                texto = "classe {} com {} ptos".format( cc, trainingROI.size().getInfo())
                print(texto)
                arqRelatorio.write(texto + '\n')

                colecaoPontos = colecaoPontos.merge(trainingROI)

        texto = "Salvando a bacia {}".format(nbacias)
        print(texto)
        arqRelatorio.write(texto + '\n')
        arqFeitos.write(nbacias + '\n')
        saveToAsset(colecaoPontos, str(nbacias))

arqFeitos.close()
arqRelatorio.close()
