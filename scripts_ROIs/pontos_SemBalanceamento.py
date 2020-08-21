#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""
import ee
import sys
# import gee 
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


#salva ftcol para um asset
def saveToAsset(collection, name):
    #diretorio do asset
    
    optExp = {
            'collection': collection, 
            'description': name, 
            'assetId': param['outAsset'] + name           
    }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print("exportando ROIs da bacia $s ...!", name)


#retorna uma lista com as strings referentes a janela dada, por exemplo em janela 5, no ano 1999, o metodo retornaria
#['classification_1997', 'classification_1998', 'classification_1999', 'classification_2000', 'classification_2001']
#desse jeito pode-se extrair as bandas referentes as janelas
def mapeiaAnos(ano, janela, anos):

    lsBandAnos = ['classification_'+str(item) for item in anos]
    
    primeiroAno = anos[0]
    ultimoAno = anos[-1]
    indice = anos.index(ano)
    
    if ano == primeiroAno:
        return lsBandAnos[0:janela]
    
    elif ano == anos[1]:
        return lsBandAnos[0:janela]
    
    elif ano == anos[-2]:
        return lsBandAnos[-janela:]
    
    elif ano == ultimoAno:
        return lsBandAnos[-janela:]
    
    else:
        return lsBandAnos[indice-2: indice+3]

# variavel que define o metodo de amostragem. o metodo 2 balanceia por area 
# e por representatividade estatistica
# baciasFeitas = [] 

def iterate_bacias(bacia, colAnos, nomeBacia):
    #colecao responsavel por executar o controle de execucao, caso optem por executar o codigo em terminais paralelos,
    #ou seja, em mais de um terminal simultaneamente..
    #caso deseje executar num unico terminal, deixar colecao vazia. 
    
    BuffBacia = bacia.geometry()
    colecaoPontos = ee.FeatureCollection([])
    
    anoCount = 1985

    for intervalo in colAnos:    
    
        bandActiva = 'classification_' + str(anoCount)
        
        print( "banda activa: " + bandActiva)
        #print("de ", intervalo)

        imgTemp = imgMapbiomas.select(intervalo).clip(BuffBacia)        

        # print(imgTemp.bandNames().getInfo())

        #@reducida: cria uma imagem que cada pixel diz quanto variou entre todas as bandas
        reducida =  imgTemp.reduce(ee.Reducer.countDistinct())
        reducida = reducida.eq(1)

        #@imgTemp: sera o mapa de uso e cobertura Mapbiomas ao que sera masked com as classes 
        #estaveis na janela de 5 anos 
        imgTemp = imgTemp.select(bandActiva)

        # processo de masked da imagem mapa mapbiomas com 2 bandas adicionais Longitude Latitude
        imgTemp = imgTemp.mask(reducida).rename(['class'])
        imgTemp = imgTemp.clip(BuffBacia)
        imgTemp = imgTemp.set("system:footprint", BuffBacia)

        # mosaicosBaciaAno = 

        mosaicosBaciaAno = ee.Image(mosaicos\
            .filter(ee.Filter.eq('year', anoCount))\
            .filterBounds(BuffBacia).mosaic()).clip(BuffBacia)
        
        mosaicosBaciaAno = mosaicosBaciaAno.addBands(imgTemp)
        mosaicosBaciaAno = mosaicosBaciaAno.mask(reducida)        
        mosaicosBaciaAno = mosaicosBaciaAno.set("system:footprint", BuffBacia)

        # print(mosaicosBaciaAno.bandNames().getInfo())
        # print("classes a serem coletada ", param['lsClasse'])
        # print("quatidade de ptos X classes ", param['lsPtos'])
        
        #print(mosaicosBaciaAno.bandNames().getInfo())
        #opcoes para o sorteio estratificadoBuffBacia

        ptosTemp = mosaicosBaciaAno.stratifiedSample(
            numPoints= 0,
            classBand= 'class',
            region= BuffBacia,
            scale= 30,
            classValues= param['lsClasse'],
            classPoints= param['lsPtos'],
            tileScale= 2,
            geometries= True
        )


        #print(ptosTemp.limit(20).size().getInfo())
        #insere informacoes em cada ft
        ptosTemp = ptosTemp.map(lambda ponto: ponto.set({'year': anoCount}))
        ptosTemp = ptosTemp.map(lambda ponto: ponto.set({'bacia': nomeBacia}))
        #ptosTemp = ptosTemp.map(lambda ponto: ponto.setGeometry(ee.Geometry.Point(ee.List([ponto.get('longitude'), ponto.get('latitude')]))))
        
        ptosTemp = ptosTemp.filter(ee.Filter.notNull(['amp_evi2', 'amp_gv', 'amp_ndfi', 'amp_ndvi', 'amp_ndwi']))
        # print(ptosTemp.first().getInfo()['properties'])
        
        #merge com colecoes anteriores 
        colecaoPontos = colecaoPontos.merge(ptosTemp)
        
        anoCount+=1
    # print(colecaoPontos.propertyNames().getInfo())
    saveToAsset(colecaoPontos, str(nomeBacia))
    


param = {
    'bioma': "CAATINGA", #nome do bioma setado nos metadados
    'asset_bacias': 'users/diegocosta/baciasRecticadaCaatinga',
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',    
    'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/BACIA_PEQUENA_SEM_BALANCEAR/',
    'assetMapbiomasP': 'projects/mapbiomas-workspace/public/collection4_1/mapbiomas_collection41_integration_v1',
    'asset_Mosaic': 'projects/mapbiomas-workspace/MOSAICOS/workspace-c3',
    'classMapB': [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33],
    'classNew': [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33],
    'janela': 5,
    'lsClasse': [3,4,12,21,22,33,29],
    'lsPtos': [1500,1500,1500,1500,1500,1500,1500] 
}

terrain = ee.Image("JAXA/ALOS/AW3D30_V1_1").select("AVE")
slope = ee.Terrain.slope(terrain)
square = ee.Kernel.square(**{'radius': 3}) 

limite_bioma = ee.Geometry.Polygon(arqParam.lsPtos_limite_bioma)

biomas = ee.FeatureCollection(param['asset_IBGE']).filter(
    ee.Filter.eq('CD_LEGENDA', param['bioma']))

# ftcol poligonos com as bacias da caatinga
ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])

#converte os anos em numeros do gee
list_anos = [k for k in range(1985,2019)]
print('lista de anos', list_anos)

# @collection1: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
# collection1 = ee.ImageCollection(dirsamples).filterMetadata('biome', 'equals', bioma)
collection41 = ee.Image(param['assetMapbiomasP']).clip(biomas.geometry())

# @mosaicos: ImageCollection com os mosaicos de Mapbiomas 
mosaicos = ee.ImageCollection(param['asset_Mosaic']).filter(ee.Filter.eq('biome',  param['bioma']))
# nameBacias = ftcol_bacias.reduceColumns(ee.Reducer.toList(), ['ID_NIVEL2']).get('list').getInfo()

# Remap todas as imagens mapbiomas
lsBndMapBiomnas = []
imgMapbiomas = ee.Image().toByte()
for year in list_anos:

    band = 'classification_' + str(year)
    lsBndMapBiomnas.append(band)

    imgTemp = collection41.select(band).remap(param['classMapB'], param['classNew'])

    imgMapbiomas = imgMapbiomas.addBands(imgTemp.rename(band))


imgMapbiomas = imgMapbiomas.select(lsBndMapBiomnas)
collection41 = None

# colecao de integracao do mapbiomas
# lista_janela = ee.List([]);
#tamanho da janela de estabilidade


# trasforma a ftcol em lista para poder iterar nela com um loop nativo
# ft_bacias = ftcol_bacias.toList(ftcol_bacias.size())

lsBacias = ftcol_bacias.reduceColumns(ee.Reducer.toList(), ['nunivotto3']).get('list').getInfo()
print("quantidade de Bacias Hidrográficas: {} ".format(len(lsBacias)))

#############################################################################
# '759', '7611','766','767','771',7612','7613','7614','7615','772', '773', 
# '774', '775', '777','776', '763','7618', '765',  '762', '746', '7619', 
# '7616', '7617', '744', '745', '747', '732', '743', '742', '741','752',
#  '753', '751','754', '756', '755','758' , '757'
#############################################################################
arqFeitos = open("listaBaciasROIsfeitas.txt", 'r')

baciasFeitas = [] 
print("listando Bacias Feitas")
for ii in arqFeitos.readlines():    
    ii = ii[:-1]
    print(" => " + str(ii))
    baciasFeitas.append(ii)

arqFeitos = open("listaBaciasROIsfeitas.txt", 'a+')


colectAnos = map(lambda ano: mapeiaAnos(ano, param['janela'], list_anos), list_anos)
newColectAnos = [k for k in colectAnos]
colectAnos = None
# print("listando as janelas names bandas")
# for intervalo in newColectAnos[:3]:         
#     print("+>", intervalo)

#faz a extracao das amostras para cada bacia
for item in lsBacias:
    
    if item not in baciasFeitas:        
    
        baciaTemp = ftcol_bacias.filter(ee.Filter.eq('nunivotto3', item)).first()
        print(baciaTemp.getInfo()['properties'])
        
        iterate_bacias(ee.Feature(baciaTemp), newColectAnos, item)
        print("salvando ROIs bacia: << {} >>".format(item))

        arqFeitos.write(item +'\n')
    
arqFeitos.close()
