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


param = {
    'lsBiomas': ['CAATINGA'],
    'asset_bacias': 'users/nerivaldogeo/bacias_caatinga_f',
    'assetBiomas' : "users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas",
    'assetpointLapig': 'projects/mapbiomas-workspace/VALIDACAO/MAPBIOMAS_100K_POINTS_utf8',    
    'assetCol5': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/classificacoes/classesV7_filter/CA_col5_v7_4055',
    'classMapB': [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33],
    'classNew': [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33],
    'pts_remap' : {
        "Formação Florestal": 3,
        "Formação Savânica": 4,        
        "Mangue": 3,
        "Floresta Plantada": 3,
        "Formação Campestre": 12,
        "Outra Formação Natural Não Florestal":12,
        "Pastagem Cultivada": 21,
        "Aquicultura": 21,
        "Cultura Perene": 21,
        "Cultura Semi-Perene": 21,
        "Cultura Anual": 21,
        "Mineração": 22,
        "Praia e Duna": 22,
        "Afloramento Rochoso": 29,
        "Infraestrutura Urbana": 22,
        "Outra Área Não Vegetada": 22,
        "Rio, Lago e Oceano": 33,
        "Não Observado": 27       
    },
    'anoInicial': 1985,
    'anoFinal': 2019,
    'numeroTask': 6,
    'numeroLimit': 2,
    'conta' : {
        '0': 'caatinga01'              
    },
    'lsProp': ['ESTADO','LON','LAT','PESO_AMOS','PROB_AMOS','REGIAO','TARGET_FID','UF'],
    "amostrarImg": True
}


#lista de anos
list_anos = [str(k) for k in range(param['anoInicial'],param['anoFinal'])]

#print('lista de anos', list_anos)
lsAllprop = param['lsProp'].copy()
for ano in list_anos:
    band = 'CLASS_' + str(ano)
    lsAllprop.append(band) 

pointTrue = ee.FeatureCollection(param['assetpointLapig']).filter(
                    ee.Filter.inList('BIOMA',  param['lsBiomas']))


print("Carregamos {} points ".format(9738))  # pointTrue.size().getInfo()
# ftcol poligonos com as bacias da caatinga
ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])

#nome das bacias que fazem parte do bioma
nameBacias = [
      '732','741','742','743','744', '745','746','747','751','752',
      '753', '754','755','756','757','758','759','762','763','764','765',
      '766','767','771','772','773', '774', '775','776','777','778',
      '76111','76116','7612','7613','7614','7615','7616', '7617','7618','7619'
]


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
def processoExportar(ROIsFeat, nameT):  
    
    optExp = {
          'collection': ROIsFeat, 
          'description': nameT, 
          'folder':"ptosCol5"          
        }
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print("salvando ... " + nameT + "..!")
    # print(task.status())
    

pointAcc = ee.FeatureCollection([])
mapClasses = ee.List([])


mapClass = ee.Image(param['assetCol5']).byte()
    
for _nbacia in nameBacias:
    
    # nameImg = 'RF_BACIA_' + _nbacia + '_RF-v3_baciaC5'
    nameImg = 'RF_BACIA_' + _nbacia 

    baciaTemp = ftcol_bacias.filter(ee.Filter.eq('nunivotto3', _nbacia))

    if param['amostrarImg'] == True:
        # print("cortou a imagem")
        mapClassTemp = mapClass.clip(baciaTemp).byte()
    
    else:
        # clipamos porque a classification esta se salvando de maior area
        mapClassTemp = ee.Image(param['assetCol5'] + nameImg).clip(baciaTemp).byte()

    pointTrueTemp = pointTrue.filterBounds(baciaTemp)

    pointAccTemp = mapClassTemp.sampleRegions(
        collection= pointTrueTemp, 
        properties= lsAllprop, 
        scale= 30,  
        geometries= False)

    pointAccTemp = pointAccTemp.map(lambda Feat: Feat.set('bacia', _nbacia))

    pointAcc = pointAcc.merge(pointAccTemp)

## Revisando todos as Bacias que foram feitas 

# cont = 0
# cont = gerenciador(cont, param)

param['lsProp'].append('bacia')
print(pointAcc.first().getInfo())

pointAll = ee.FeatureCollection([])

lsNameClass = [kk for kk in param['pts_remap'].keys()]
lsValClass = [kk for kk in param['pts_remap'].values()]

for ano in list_anos:    
    
    labelRef = 'CLASS_' + str(ano)
    print("label de referencia : " + labelRef)
    labelCla = 'classification_' + str(ano)
    print("label da classification : " + labelCla)

    newProp = param['lsProp'] + [labelRef, labelCla]
    print("lista de propeties", newProp)
    newPropCh = param['lsProp'] + ['reference', 'classification']

    FeatTemp = pointAcc.select(newProp)
    #print(FeatTemp.first().getInfo())
    FeatTemp = FeatTemp.remap(lsNameClass, lsValClass, labelRef)   

    FeatTemp = FeatTemp.select(newProp, newPropCh)

    FeatTemp = FeatTemp.map(lambda  Feat: Feat.set('year', str(ano)))
    #print(FeatTemp.first().getInfo())

    pointAll = pointAll.merge(FeatTemp)

extra = param['assetCol5'].split('/')

if param['amostrarImg'] == True:
    name = 'occTabela_Caatinga_' + extra[-1]
else:
    name = 'occTabela_Caatinga_' + extra[-2]
processoExportar(pointAll, name)               

