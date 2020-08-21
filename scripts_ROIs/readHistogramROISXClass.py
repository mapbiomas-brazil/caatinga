#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee 
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

param = {
    'bioma': "CAATINGA", #nome do bioma setado nos metadados
    'asset_bacias': 'users/diegocosta/baciasRecticadaCaatinga',
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',    
    'assetROIs': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/ROIsXBaciasBalmin300v3'},    
    'lsClass': ['3','4','12','21','22','29','33'], 
    'lsROIs' : {
        '0': 'PtosXBaciasBalanceados',
        '1': 'ROIsXBaciasBalClusterv2',
        '2': 'ROIsXBaciasBalmin300v3',
        '3': 'ROIsXBaciasBalv2',
        '4': 'RoisSmoteBacias'
    }
}


def GetPolygonsfromFolder(lsNaBacias):
    
    getlistPtos = ee.data.getList(param['assetROIs'])

    ColectionPtos = ee.FeatureCollection([])
    
    for idAsset in getlistPtos: 
        
        path_ = idAsset.get('id')
        # print(path_) 
        
        lsFile =  path_.split("/")
        name = lsFile[-1]
        newName = name.split('_')

        if newName[0] in lsNaBacias:

            # print(path_)

            FeatTemp = ee.FeatureCollection(path_)
    
            ColectionPtos = ColectionPtos.merge(FeatTemp)

    ColectionPtos = ee.FeatureCollection(ColectionPtos)#.flatten()
        
    return  ColectionPtos



list_anos = [k for k in range(1985,2019)]
# print('lista de anos', list_anos)

_bacias =  ee.FeatureCollection(param['asset_bacias'])

#nome das bacias que fazem parte do bioma
nameBacias = arqParam.listaNameBacias
# print(nameBacias)

lstResult = []

linha = 'Anos,Bacia,cc3,cc4,cc12,cc21,cc22,cc29,cc33,Total\n'
lstResult.append(linha)
# for ii in range(5):
for ano in list_anos:
    print("#####################################################")
    print("##########ANO ## {} #########################".format(ano))
    

    for baciaIter  in nameBacias:   
        linha = str(ano) + ','
        texto = "procesando a Bacia " + baciaIter
        print(texto) 
        linha += baciaIter + ','            

        #pasta contendo os pontos das bacias
        ROIs = GetPolygonsfromFolder(baciaIter)
        temptraining = ROIs.filter(ee.Filter.eq('year',  ano))
            
        # texto = "tamanho do ROis para treino: " + str(temptraining.size().getInfo())
        # print(texto) 
        
        histog = temptraining.aggregate_histogram('class').getInfo()
        print(histog)
        nKeys = [kk for kk in histog.keys()]
        sum = 0
        for cc in param['lsClass']:
            
            if cc in nKeys:
                linha += str(histog[cc]) + ','
                sum += int(histog[cc])

            else: 
                linha += '0,'
        
        linha += str(sum) + '\n'
        lstResult.append(linha)

nomeArq = param['assetROIs']['id'].split('/')
nomeArq = 'ocorrencia/histogram_' + nomeArq[-1] + '.csv'
arqHistogCSV = open(nomeArq, 'w')

for linha in lstResult:

    arqHistogCSV.write(linha)

arqHistogCSV.close()