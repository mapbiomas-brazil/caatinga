#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee 
import gee
import json
import csv
import sys

try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
sys.setrecursionlimit(1000000000)


param = {
    
    'assetROIs': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/ROIsXBaciasBalmin300v3'},
    'anoInicial': 1985,
    'anoFinal': 2019,
    'numeroTask': 6,
    'numeroLimit': 4,
    'conta' : {
        '0': 'caatinga04'              
    },

}

#lista de anos
# list_anos = [k for k in range(param['anoInicial'],param['anoFinal'])]
# print('lista de anos', list_anos)

#nome das bacias que fazem parte do bioma (38 bacias)
nameBacias = [
      '732','741','742','743','744', '745','746','747','751','752',
      '753', '754','755','756','757','758','759','762','763','765',
      '766','767','771','772','773', '774', '775','776','777',
      '7611','7612','7613','7614','7615','7616', '7617','7618','7619'
]

#========================METODOS=============================
#========================METODOS=============================
def gerenciador(cont, param):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]

    if str(cont) in numberofChange:
        
        gee.switch_user(param['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
    elif cont > param['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont

#exporta a imagem classificada para o asset
def processoExportar(ROIsFeat, nameB):
    
    nomeDesc = 'RF_BACIA_'+ str(nameB) + '_' 
    
    optExp = {
          'collection': ROIsFeat, 
          'description': nomeDesc, 
          'folder':"ROIsClusterC1"          
        }
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print("salvando ... " + nomeDesc + "..!")
    

# carregando os ROIs de uma bacia especifica 
def GetPolygonsfromFolder(nBacias):
    
    getlistPtos = ee.data.getList(param['assetROIs'])

    ColectionPtos = ee.FeatureCollection([])
    
    for idAsset in getlistPtos: 
        
        path_ = idAsset.get('id')
        # print(path_) 
        
        lsFile =  path_.split("/")
        name = lsFile[-1]
        newName = name.split('_')

        if newName[0] == nBacias:

            print("carregando bacia: " + name)

            FeatTemp = ee.FeatureCollection(path_)
    
            ColectionPtos = ColectionPtos.merge(FeatTemp)

    ColectionPtos = ee.FeatureCollection(ColectionPtos)
        
    return  ColectionPtos


## Revisando todos as Bacias que foram feitas 
arqFeitos = open("registros/lsBaciasROIs300.txt", 'r')

baciasFeitas = [] 

for ii in arqFeitos.readlines():    
    ii = ii[:-1]
    baciasFeitas.append(ii)


arqFeitos = open("registros/lsBaciasROIs300.txt", 'a+')
cont = 0
cont = gerenciador(cont, param)
for _nbacia in nameBacias:
    
    if _nbacia not in baciasFeitas:

        print("Carregando a bacia " + _nbacia) 

        ROIs = GetPolygonsfromFolder(_nbacia)          

        processoExportar(ROIs, _nbacia)               

        arqFeitos.write(_nbacia + '\n')

arqFeitos.close()