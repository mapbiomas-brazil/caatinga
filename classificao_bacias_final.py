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



#============================================================

param = {
    'bioma': ["CAATINGA",'CERRADO','MATAATLANTICA'], #nome do bioma setado nos metadados
    'asset_bacias': "users/nerivaldogeo/bacias_caatinga_f",
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',
    # 'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/classificacoes/classesV1/',
    #'assetROIs': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/ROIsXBaciasBalClusterv2'},
    # 'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/classificacoes/classesV5/',
    # 'assetROIs': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/ROIsXBaciasBalmin300v3'},
    # 'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/classificacoes/classesV6/',
    # 'assetROIs': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/RoisSmoteBacias'},
    'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/classificacoes/classesV11/',
    'assetROIs': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col4/CAATINGA/PtosBacias2_1000'},
    'assetMapbiomasP': 'projects/mapbiomas-workspace/public/collection4_1/mapbiomas_collection41_integration_v1',
    'asset_Mosaic': 'projects/mapbiomas-workspace/MOSAICOS/workspace-c3',    
    'classMapB': [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33],
    'classNew': [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33],
    'anoInicial': 1985,
    'anoFinal': 2019,
    "anoIntInit": 2005,
    "anoIntFin": 2018,
    'sufix': "_03",    
    'lsBandasMap': [],
    'numeroTask': 6,
    'numeroLimit': 40,
    'conta' : {
        '0': 'caatinga01',
        '6': 'caatinga02',
        '12': 'caatinga03',
        '18': 'caatinga04',
        '24': 'caatinga05',        
        '28': 'solkan1201',
        '32': 'diegoGmail',
        '35': 'rodrigo',
        # '34': 'Rafael'        
    },
    'pmtRF': {
        'numberOfTrees': 60, 
        'variablesPerSplit': 6,
        'minLeafPopulation': 3,
        'maxNodes': 10,
        'seed': 0
    } 
}


# print(param.keys())
print("vai exportar em ", param['assetOut'])
# print(param['conta'].keys())

#============================================================
#========================METODOS=============================
#============================================================

def gerenciador(cont):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]
    
    if str(cont) in numberofChange:

        print("conta ativa >> {} <<".format(param['conta'][str(cont)]))        
        gee.switch_user(param['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
    elif cont > param['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont

#exporta a imagem classificada para o asset
def processoExportar(mapaRF, regionB, nameB):
    #print(regionB)
      
    nomeDesc = 'RF_BACIA_'+ str(nameB)
    # idasset = 
    idasset =  param['assetOut'] + nomeDesc
    
    print (idasset)
    
    optExp = {'image': mapaRF, 
                 'description': nomeDesc, 
                 'assetId':idasset, 
                 'region':regionB.getInfo(), #['coordinates']
                 'scale': 30, 
                 'maxPixels': 1e13,
                 "pyramidingPolicy":{".default": "mode"}
             }
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando ... " + nomeDesc + "..!")
    # print(task.status())
    for keys, vals in dict(task.status()).items():
        print ( "  {} : {}".format(keys, vals))

#map do col anos
def map_col_pontos(table):
	mylist = table.get('id').split('/')
	FeatCPtos = ee.FeatureCollection(table.get('id')).map(lambda f: f.set('id', int(mylist[len(mylist) - 1])))
	return FeatCPtos


def GetPolygonsfromFolder(nBacias):
    
    getlistPtos = ee.data.getList(param['assetROIs'])

    ColectionPtos = ee.FeatureCollection([])

    rNBacias = []
    for bac in nBacias:
        rNBacias.append(str(bac))
    
    for idAsset in getlistPtos: 
        
        path_ = idAsset.get('id')
        # print(path_) 
        
        lsFile =  path_.split("/")
        name = lsFile[-1]
        newName = name.split('_')
        # print(newName[0])

        if newName[0] in rNBacias :

            print(path_)

            FeatTemp = ee.FeatureCollection(path_)
    
            ColectionPtos = ColectionPtos.merge(FeatTemp)

    ColectionPtos = ee.FeatureCollection(ColectionPtos)
        
    return  ColectionPtos


def FiltrandoROIsXimportancia(nROIs, baciasAll, nbacia):

    print("aqui  ")
    limitCaat = ee.FeatureCollection('users/CartasSol/shapes/nCaatingaBff3000')
    # selecionando todas as bacias vizinhas 
    baciasB = baciasAll.filter(ee.Filter.eq('nunivotto3', nbacia))
    # limitando pelo bioma novo com buffer
    baciasB = baciasB.geometry().buffer(2000).intersection(limitCaat.geometry())
    # filtrando todo o Rois pela área construida 
    redROIs = nROIs.filterBounds(baciasB)
    mhistogram = redROIs.aggregate_histogram('class').getInfo()
    ROIsEnd = ee.FeatureCollection([])
    
    roisT = ee.FeatureCollection([])
    for kk, vv in mhistogram.items():
        print("class {}: == {}".format(kk, vv))
        
        roisT = redROIs.filter(ee.Filter.eq('class', int(kk)))
        roisT =roisT.randomColumn()
        
        if int(kk) == 4:

            roisT = roisT.filter(ee.Filter.gte('random',0.5))
            # print(roisT.size().getInfo())

        elif int(kk) != 21:

            roisT = roisT.filter(ee.Filter.lte('random',0.9))
            # print(roisT.size().getInfo())

        ROIsEnd = ROIsEnd.merge(roisT)
        # roisT = None
    
    return ROIsEnd


ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])

#nome das bacias que fazem parte do bioma7619
nameBacias = arqParam.listaNameBacias
print(nameBacias)
#nome das bandas 
bandNames = ee.List([
     'median_gcvi','median_gcvi_dry','median_gcvi_wet','median_gvs','median_gvs_dry','median_gvs_wet',
     'median_hallcover','median_ndfi','median_ndfi_dry','median_ndfi_wet', 'median_ndvi','median_ndvi_dry',
     'median_ndvi_wet','median_nir_dry','median_nir_wet','median_savi_dry','median_savi_wet','median_swir1',
     'median_swir2','median_swir1_dry','median_swir1_wet','median_swir2_dry', 'median_swir2_wet','median_nir',
     'median_pri','median_red','median_savi','median_evi2','min_nir','min_red','min_swir1','min_swir2', 
     'median_fns_dry','median_ndwi_dry','median_evi2_dry','median_sefi_dry','median_ndwi','median_red_dry',
     'median_wefi_wet','median_ndwi_wet'      
     ])

#opcoes do random forest 


#lista de anos
list_anos = [k for k in range(1985,2020)]
print('lista de anos', list_anos)
param['lsBandasMap'] = ['classification_' + str(kk) for kk in list_anos]


# @mosaicos: ImageCollection com os mosaicos de Mapbiomas 
mosaicos = ee.ImageCollection(param['asset_Mosaic']).filter(
        ee.Filter.inList('biome',  param['bioma']))
        
def iterandoXBacias(bacia, nomeBacia, bRois):

    imglsClasxanos = ee.Image().byte()
    mydict = None
    primerAno = list_anos[0]
    selectBacia = bacia.filter(ee.Filter.eq('nunivotto3', nomeBacia)).first()
    selectBacia = selectBacia.geometry().buffer(2000)

    
    # i = 1
    
    for ano in list_anos:
        
        #se o ano for 2018 utilizamos os dados de 2017 para fazer a classificacao
        bandActiva = 'classification_' + str(ano)
        
        print( "banda activa: " + bandActiva)

        if ano < param['anoFinal'] - 1:
            
            temptraining = bRois.filter(ee.Filter.eq('year', int(ano)))
        
        if primerAno == ano:
            
            #pega os dados de treinamento utilizando a geometria da bacia com buffer           
            print(" Distribuição dos pontos na bacia << {} >>".format(nomeBacia))
            print("===  {}  ===".format(temptraining.aggregate_histogram('class').getInfo()))            
        
        #cria o mosaico a partir do mosaico total, cortando pelo poligono da bacia
        mosaicMapbiomas = ee.Image(mosaicos.filter(ee.Filter.eq('year', ano))\
                            .filterBounds(bacia).median()).clip(selectBacia)
        
        
        #cria o classificador com as especificacoes definidas acima 
        classifier = ee.Classifier.smileRandomForest(**param['pmtRF'])\
            .train(temptraining, 'class', bandNames)
        
        #para que na imagem classificada e agrupada cada banda corresponda a um ano
        #criamos essa variavel e passamos ela na classificacao  
        
        #classifica
        classified = mosaicMapbiomas.classify(classifier, bandActiva)
        #print("classificando!!!! ")
        #verifica se o ano em questao eh o primeiro ano 
        # condition = ee.Algorithms.IsEqual(ano, primerAno)
        
        #se for o primeiro ano cria o dicionario e seta a variavel como
        #o resultado da primeira imagem classificada
        #print("addicionando classification bands")
        if primerAno == ano:
            #print ('entrou em 1985')
            imglsClasxanos = classified
            
            mydict = {
                'id_bacia': _nbacia,
                'version': '6',
                'biome': param['bioma'],
                'collection': '5.0',
                'sensor': 'Landsat',
                'bacia': nomeBacia
            }
        #se nao, adiciona a imagem como uma banda a imagem que ja existia
        else:
            
            imglsClasxanos = imglsClasxanos.addBands(classified)
    
    # i+=1
    
    #seta as propriedades na imagem classificada            
    imglsClasxanos = imglsClasxanos.select(param['lsBandasMap'])
    imglsClasxanos = imglsClasxanos.set(mydict)
    imglsClasxanos = imglsClasxanos.set("system:footprint", selectBacia.coordinates())
    
    nomec = _nbacia + '_' + 'RF-v3_baciaC5'
    #exporta bacia
    processoExportar(imglsClasxanos, selectBacia.coordinates(), nomec) #.bounds(1).getInfo()



## Revisando todos as Bacias que foram feitas 
arqFeitos = open("registros/lsBaciasClassifyfeitasv11.txt", 'r')

baciasFeitas = [] 

for ii in arqFeitos.readlines():    
    ii = ii[:-1]
    # print(" => " + str(ii))
    baciasFeitas.append(ii)

# if len(baciasFeitas) > 0:    
#     print("listando Bacias Feitas")    
#     for ii in baciasFeitas:
#         print("==> " + ii)

arqFeitos = open("registros/lsBaciasClassifyfeitasv11.txt", 'a+')
cont = 6
for _nbacia in nameBacias:
    
    # if _nbacia not in baciasFeitas:
        
    cont = gerenciador(cont) 

    print("classificando bacia " + _nbacia)        

    selectBacia = ftcol_bacias.filter(ee.Filter.eq('nunivotto3', _nbacia)).first() 
    baciasBuff = ftcol_bacias.filterBounds(selectBacia.geometry())
    
    #lsNamesBacias = baciasBuff.reduceColumns(ee.Reducer.toList(), ['nunivotto3']).get('list').getInfo()
    #print("lista de Bacias vizinhas", lsNamesBacias) 
    if _nbacia == '76116' or _nbacia == '76111':
        lsNamesBacias = arqParam.dictBaciasViz['7611']
    else:
        lsNamesBacias = arqParam.dictBaciasViz[_nbacia]

    ROIs = GetPolygonsfromFolder(lsNamesBacias)    
    ROIs = ROIs.filter(ee.Filter.notNull(bandNames)) 
    # fROIs =  FiltrandoROIsXimportancia(ROIs, ftcol_bacias, _nbacia)   
    print("filtrou as ROIs")  
    # mhistogram = fROIs.aggregate_histogram('class').getInfo()    
    # print(mhistogram)
    # print(fROIs.first().getInfo())

    iterandoXBacias(baciasBuff, _nbacia, ROIs)                        

    # arqFeitos.write(_nbacia + '\n')

# arqFeitos.close()
