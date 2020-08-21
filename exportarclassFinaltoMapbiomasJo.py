#!/usr/bin/env python2
# -*- coding: utf-8 -*-

##########################################################
## CRIPT DE EXPORTAÇÃO DO RESULTADO FINAL PARA O ASSET  ##
## DE mAPBIOMAS                                         ##
## Produzido por Geodatin - Dados e Geoinformação       ##
##  DISTRIBUIDO COM GPLv2                               ##
#########################################################

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


def gerenciador(cont, paramet):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in paramet['conta'].keys()]
    
    if str(cont) in numberofChange:

        print("conta ativa >> {} <<".format(paramet['conta'][str(cont)]))        
        gee.switch_user(paramet['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= paramet['numeroTask'], return_list= True)        
    
    elif cont > paramet['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont


param = {
    'inputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/classificacoes/classesV7_filter/CA_col5_v7_8805',
    'outputAsset': 'projects/mapbiomas-workspace/COLECAO5/classificacao',   
    'biome': 'CAATINGA', #configure como null se for tema transversal
    'version': '4',
    'collection': 5.0,
    'source': 'geodatin',
    'theme': None, 
    'numeroTask': 0,
    'numeroLimit': 35,
    'conta' : {
        '0': 'caatinga01',
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',        
        '24': 'solkan1201',
        '28': 'diegoGmail',
        '32': 'rodrigo',
        # '34': 'Rafael'        
    },
}
metadados = {}
# bioma250mil = ee.FeatureCollection('projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil')\
#                .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry().buffer(3000)

bioma250mil = ee.FeatureCollection('users/CartasSol/shapes/nCaatingaBff3000').geometry()

imageMap = ee.Image(param['inputAsset'])
geomet = imageMap.geometry()

for ii, year in enumerate(range(1985,2020)):
    
    gerenciador(ii, param)
    bandaAct = 'classification_' + str(year) 
    print("Banda activa: " + bandaAct)

    imgYear = imageMap.select([bandaAct], ['classification'])
        
    imgYear = imgYear.clip(bioma250mil)
    imgYear = imgYear.set('biome', param['biome'])\
                    .set('year', year)\
                    .set('version', param['version'])\
                    .set('collection', param['collection'])\
                    .set('source', param['source'])\
                    .set('system:footprint', bioma250mil)    

    
    name = param['biome'] + '-' + str(year) + '-' + param['version']

    optExp = {   
        'image': imgYear.byte(), 
        'description': name, 
        'assetId':param['outputAsset'] + '/' + name, 
        'region':bioma250mil, #.getInfo()['coordinates']
        'scale': 30, 
        'maxPixels': 1e13,
        "pyramidingPolicy": {".default": "mode"}
    }

    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando ... banda  " + name + "..!")