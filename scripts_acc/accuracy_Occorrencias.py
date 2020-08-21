import sys
import os
import glob
import pandas as pd 

import math
import DictClassMod2

import warnings

from os import path, makedirs
import csv
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import confusion_matrix, precision_score, recall_score, accuracy_score, f1_score
from sklearn.utils.multiclass import unique_labels

path = os.getcwd()
# print("path of folder work ==> \n",str(path))

input_dir = str(path) + "/INPUT_C/" #sys.argv[1]
# print("path of folders of files .csv inputs\n  ==>  {}".format(input_dir))

output_dir =  str(path) + '/NEWOUTPUT_COL4_CAAT2/' #sys.argv[2]
# print("path of  folders of files .csv OUTUTS\n  ==> {}".format(output_dir))


POINTS_FILE = "occTabela_Caatinga_classesV7.csv"


numeroClases = 4

IGNORED_CLASSES = [0,31,32,30,25,23,5,29]

ALL_CLASSES = DictClassMod2.ALL_CLASSES

def get_classes(df, level='l1'):

	class_values = {}
	class_names = {}

	clas_classes = pd.Index(df['classification'].unique())
	ref_classes = pd.Index(df['reference'].unique())

	acc_classes = clas_classes.intersection(ref_classes)

	val_remap = {}

	for value in ALL_CLASSES.keys():
		if (value not in IGNORED_CLASSES and (value in acc_classes)):
			
			val_key = "%s_val" % (level)
			new_val = ALL_CLASSES[value][val_key]
			class_name = ALL_CLASSES[value][level]

			val_remap[value] = new_val
			class_values[new_val] = True
			class_names[class_name] = True

	df = df[df['classification'].isin(val_remap.keys())]
	df = df[df['reference'].isin(val_remap.keys())]

	df['classification'] = df['classification'].map(val_remap)
	df['reference'] = df['reference'].map(val_remap)
	class_values = list(class_values.keys())
	class_names = list(class_names.keys())

	return df, class_values, class_names

def read_csvs(pathTable):	
	
	df_csv = pd.read_csv(input_dir + pathTable)
	
	dfTemp = calculate_prob(df_csv)

	return dfTemp

def classification_report_shinny(df, level, class_names, class_values, region, year):
	
	header = []
	rows = []
	footer = []

	y_true = df[['reference']].to_numpy().flatten()
	y_pred = df[['classification']].to_numpy().flatten()
	sample_weight = 1 / df[['prob_amos']].to_numpy().flatten()
	matrix = confusion_matrix(y_true, y_pred, sample_weight=sample_weight)

	glob_acc, glob_se = global_acc(df)
	
	user_acc, prod_acc, user_se, prod_se = user_prod_acc(df, class_values)
	refarea_prop, refarea_se = refarea_pop(df, class_values)
	map_bias, map_bias_se = calc_map_bias(df, class_values)

	matrix = matrix.transpose()
	estimated_pop = sample_weight.sum()

	matrix = (matrix / estimated_pop)

	header = [' ']
	header += class_names
	header += ["total", "population", "population bias"]
	header += ["user's accuracy", "user stderr"]
	header += ["error of comission", "area dis"]

	total_col = matrix.sum(axis=0)
	total_row = matrix.sum(axis=1)

	user_acc_tot = np.sum(user_acc * total_row)
	user_se_tot = np.sum(user_se * total_row)

	prod_acc_tot = np.sum(prod_acc * total_col)
	prod_se_tot = np.sum(prod_se * total_col)

	quantity_dis = np.absolute(total_row - total_col)
	allocation_dis = 2 * np.minimum((total_row - np.diagonal(matrix)), (total_col - np.diagonal(matrix)))

	quantity_dis_tot = np.sum(quantity_dis) / 2
	allocation_dis_tot = np.sum(allocation_dis) / 2

	#print(str(level) + ';' + region + ';' + str(glob_acc*100) + ';' + str(quantity_dis_tot*100) + ';' + str(allocation_dis_tot*100))
	#return []

	fmt = '.3f'
	metric_fmt = '.3f'
	for i in range(matrix.shape[0]):
		row = [class_names[i]]
		for j in range(matrix.shape[1]):
			row.append(matrix[i, j])
		row.append(total_row[i])
		row.append(total_row[i])
		row.append(map_bias[i])
		row.append(user_acc[i])
		row.append(user_se[i])
		row.append((1 - user_acc[i]))
		row.append( quantity_dis[i] )

		rows.append(row)

	na_fill = ['NA', 'NA', 'NA', 'NA', 'NA', 'NA']
	
	total = ['total']
	total += ( col for col in total_col.tolist())
	total += [ np.sum(refarea_prop), np.sum(refarea_prop), 0, user_acc_tot, user_se_tot, (1-user_acc_tot), quantity_dis_tot ]

	r_adj_pop = ['adj population']
	r_adj_pop += ( col for col in refarea_prop)
	r_adj_pop += [np.sum(refarea_prop)]
	r_adj_pop += na_fill

	r_adj_pop_se = ['adj pop stdErr']
	r_adj_pop_se += ( col for col in refarea_se)
	r_adj_pop_se += [np.sum(refarea_se)]
	r_adj_pop_se += na_fill
	
	r_prod_acc = ["producer's accuracy"]
	r_prod_acc += ( col for col in prod_acc)
	r_prod_acc += [prod_acc_tot]
	r_prod_acc += na_fill

	r_prod_se = ["prod stdErr"]
	r_prod_se += ( col for col in prod_se)
	r_prod_se += [prod_se_tot]
	r_prod_se += na_fill

	r_omiss = ["error of omission"]
	r_omiss += ( (1 - col) for col in prod_se)
	r_omiss += [(1 - prod_acc_tot)]
	r_omiss += na_fill

	r_alloc_dis = ["alloc dis"]
	r_alloc_dis += ( col for col in allocation_dis)
	r_alloc_dis += [allocation_dis_tot]
	r_alloc_dis += na_fill

	result = [[" "]]
	result += [[" "]]
	result += [[" ANO: " + str(year) + " "]]
	result += [header]
	result += rows
	result += [total]
	result += [r_adj_pop]
	result += [r_adj_pop_se]
	result += [r_prod_acc]
	result += [r_prod_se]
	result += [r_omiss]
	result += [r_alloc_dis]

	return result

def classification_report(df, class_names, class_values, region, year):
	
	header = []
	rows = []
	footer = []

	y_true = df[['reference']].to_numpy().flatten()
	y_pred = df[['classification']].to_numpy().flatten()
	sample_weight = 1 / df[['prob_amos']].to_numpy().flatten()
	matrix = confusion_matrix(y_true, y_pred)
	
	total_col = matrix.sum(axis=0)
	total_row = matrix.sum(axis=1)

	fmt = '.3f'
	metric_fmt = '.3f'
	for i in range(matrix.shape[0]):
		row = [region, year, class_names[i]]
		row.append('')
		row.append('')
		row.append(format(prod_acc[i], metric_fmt))
		row.append(format(prod_se[i], metric_fmt))
		row.append(format(user_acc[i], metric_fmt))
		row.append(format(user_se[i], metric_fmt))
		for j in range(matrix.shape[1]):
			row.append(format(matrix[i, j], fmt))
		row.append(format(total_row[i], fmt))
		row.append(format(map_bias[i], fmt))
		row.append(format(map_bias_se[i], fmt))

		rows.append(row)

	footer = [region, year, 'Prop.area (Pontos)']

	footer += [ format(glob_acc,metric_fmt) ] 
	footer += [ format(glob_se,metric_fmt) ] 
	footer += [ '-', '-', '-', '-' ]
	footer += ( format(col, fmt) for col in total_col.tolist())
	footer += [ format(total_col.sum(), fmt) ]

	footer2 = [region, year, 'Prop.area.se (Pontos)']

	footer2 += [ '-','-','-', '-', '-', '-' ] 
	footer2 += ( format(col, fmt) for col in refarea_se)
	footer2 += [ format(np.sum(refarea_se), fmt) ]
	
	#stand_error = calculate_stand_error(df, estimated_pop)
	#print(region, cur_class, stand_error)

	result = [header]
	result += rows
	result += [footer, footer2]

	return result

def save_csv(output_filename, data):
	with open(output_filename, encoding='latin-1', mode='w') as output_file:
		print("Generating " + output_filename)
		csv_writer = csv.writer(output_file, delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
		csv_writer.writerows(data)

def calculate_prob(dfT):
	columnas = ['system:index', 'classes', 'cluster', 'latitude_209564535', 'longitude_209564535', '.geo']
	
	valsClasses = [1,2,3,4]
	
	MatConf = np.zeros([numeroClases+1, numeroClases+1], dtype = int)
	# print(MatConf)
	dfT.columns = columnas	
	# print("Columnas {}".format(dfT.columns))
	print("tamanho do dataframe: {}".format(dfT.shape))

	
	for ccs in valsClasses:
		for clc in valsClasses:
			
			expresion = 'classes == ' + str(ccs) + " and cluster == " + str(clc)
			# print("expresion ", expresion)

			valoresdict = dfT.query(expresion)
			valor = valoresdict.shape[0]
			MatConf[ccs-1 ,clc -1] = valor
			# print(valor)

	
	MatConf[numeroClases, :] = np.sum(MatConf, axis = 0)
	MatConf[:, numeroClases] = np.sum(MatConf, axis = 1)	

	print("revisa a matriz \n", MatConf)	

	return []

def mkdirp(path):
	try:
		makedirs(path)
	except:
		pass

def accuracy_assessment_all(df, biome='BRASIL'):
	
	#['l2', 'l3', 'l1']
	for level in ['l1']:

		# acc_output_dir = path.join(output_dir, level)
		acc_output_dir = output_dir + level
		
		mkdirp(acc_output_dir)

		# output_filename = path.join(acc_output_dir, ''.join(['acc_int_', str(biome), '.csv']))
		output_filename = acc_output_dir + 'acc_int_' + str(biome) + '.csv'

		years = df['year'].unique()
		years.sort()

		result = [["Thu Jan 11 18:27:46 2018   Matrizes de confusão anuais para " + biome + "  -  Coleção 4.0 (CLASSIFICAÇÃO + FILTRO + INTEGRAÇÃO)  "]]
		result += [[" "]]
		result += [["Corpo da tabela contém distribuição de frequências cruzadas da amostra."]]
		result += [["Marginais:"]]
		result += [["Totais: A coluna 'total' contém a soma das amostras de cada classe mapeada ou a estatística de linha para todas as classes. A linha 'total' contém a soma das amostras em cada classe observada ou a respectiva estatística de coluna para todas as classes. "]]
		result += [["Número de píxeis na população - A coluna 'population' contém o número de píxeis totais de cada classe mapeada. A 'adj population' contém as estimativas no número de píxeis na população corrigida pela matriz de erros. A coluna 'bias' contém a estimativa do viés relativo da área mapeada. A linha 'adj pop stdErr' contém uma estimativa do erro padrão do número de píxeis corrigido. Usado para representar a incerteza d ou construir intervalos de confiança. A estimativa do erro padrão é confiável apenas quando n>30./nAcurácias - Acurácia do usuário (user's accuracy): estimativa da fração de píxeis (ou área) de cada classe do mapa que está corretamente mapeada. Acurácia do produtor (producer's accuracy): estimativa da fração de píxeis (ou área) de cada classe que foi corretamente mapeada. A coluna 'user stderr' contém a estimativa do erro padrão da acurácia do usuário"]]
		result += [["Erros - Erro de comissão e omissão: são os complementares da acurácia do usuário e produtor"]]
		result += [["Decomposição do erro - O erro é decomposto em 'discordância de área' (area dis) e 'discordância de alocação' (alloc dis). A soma deles é o erro total."]]

		for year in years:
			result += accuracy_assessment(df, level, year, biome)

		result += accuracy_assessment(df, level, 'Todos', biome)

		save_csv(output_filename, result)

def accuracy_assessment(df, level='l1', year='Todos', biome='BRASIL'):

	df = df.copy(deep=True)
	
	if year != 'Todos':
		df = df[df['year'] == year]

	if biome != 'BRASIL':
		df = df[df['BIOMA'] == biome]
	
	df, class_values, class_names = get_classes(df, level)

	return classification_report_shinny(df, level, class_names, class_values, biome, year)

def population_estimation(df):
	sample_weight = 1 / df[['prob_amos']].to_numpy().flatten()
	return sample_weight.sum()

def covariance(x, y):
	if x.size < 1:
		x_mean = np.mean(x)
		y_mean = np.mean(y)

		return np.sum((x - x_mean) * (y - y_mean) / (x.size - 1))
	else:
		return 0.0

def user_prod_se(df, class_val, user_acc, prod_acc, map_total, ref_total):
	
	user_var = 0
	prod_var = 0

	user_se = 0
	prod_se = 0

	for name, df_strata in df.groupby('strata_id'):
		
		ref_val_s = df_strata['reference'].to_numpy()
		map_val_s = df_strata['classification'].to_numpy()

		map_total_s = np.where((map_val_s == class_val), 1, 0)
		map_correct_s = np.where(np.logical_and((map_val_s == class_val),(map_val_s == ref_val_s)), 1, 0)

		ref_total_s = np.where((ref_val_s == class_val), 1, 0)
		ref_correct_s = np.where(np.logical_and((ref_val_s == class_val),(map_val_s == ref_val_s)), 1, 0)
		
		nsamples_s, _ = df_strata.shape
		population_s = population_estimation(df_strata)

		user_var += math.pow(population_s,2) * (1 - nsamples_s/population_s) \
									* ( math.pow(	np.var(map_correct_s) , 2) \
											+ user_acc * math.pow( np.var(map_total_s) , 2) \
											- 2 * user_acc * covariance(map_total_s, map_correct_s) \
 										) / nsamples_s

		prod_var += math.pow(population_s,2) * (1 - nsamples_s/population_s) \
									* ( math.pow(	np.var(ref_correct_s) , 2) \
											+ prod_acc * math.pow( np.var(ref_total_s) , 2) \
											- 2 * prod_acc * covariance(ref_total_s, ref_correct_s) \
 										) / nsamples_s

	if (map_total !=0):
		user_var = 1 / math.pow(map_total,2) * user_var
		user_se = 1.96 * math.sqrt(user_var)

	if (ref_total !=0):
		prod_var = 1 / math.pow(ref_total,2) * prod_var
		prod_se = 1.96 * math.sqrt(prod_var)

	return user_se, prod_se

def global_se(df, mask, population):
	glob_var = 0

	for name, df_strata in df.groupby('strata_id'):
		
		ref_val_s = df['reference'].to_numpy()
		map_val_s = df['classification'].to_numpy()

		map_correct_s = np.where( mask, 1, 0)

		nsamples_s, _ = df_strata.shape
		population_s = population_estimation(df_strata)
		glob_var += math.pow(population_s,2) * (1 - nsamples_s/population_s) \
								* np.var(map_correct_s) / nsamples_s

	glob_var = 1 / math.pow(population,2) * glob_var
	glob_se = 1.96 * math.sqrt(glob_var)

	return glob_se

def calc_map_bias(df, class_values):

	map_bias_arr = []
	map_bias_se_arr = []

	ref_val = df['reference'].to_numpy()
	map_val = df['classification'].to_numpy()
	samp_weight = 1 / df['prob_amos'].to_numpy()

	population = population_estimation(df)

	for class_val in class_values:
	
		map_mask = np.logical_and((map_val == class_val), (ref_val != class_val))
		map_comission_prop = np.sum(np.where(map_mask, 1, 0) * samp_weight) / population

		ref_mask = np.logical_and((ref_val == class_val), (map_val != class_val))
		map_omission_prop = np.sum(np.where(ref_mask, 1, 0) * samp_weight) / population

		map_bias = (map_omission_prop - map_comission_prop)
		
		se_mask = np.logical_xor(ref_mask,map_mask)
		map_bias_se = global_se(df, se_mask, population)

		map_bias_arr.append(map_bias)
		map_bias_se_arr.append(map_bias_se)

	return map_bias_arr, map_bias_se_arr

def refarea_pop(df, class_values):

	refarea_prop_arr = []
	refarea_se_arr = []

	ref_val = df['reference'].to_numpy()
	map_val = df['classification'].to_numpy()
	
	samp_weight = 1 / df['prob_amos'].to_numpy()

	population = population_estimation(df)

	for class_val in class_values:
	
		ref_mask = (ref_val == class_val)
		refarea = np.sum(np.where(ref_mask, 1, 0) * samp_weight)

		refarea_prop = (refarea / population)
		refarea_se = global_se(df, ref_mask, population)

		refarea_prop_arr.append(refarea_prop)
		refarea_se_arr.append(refarea_se)

	return refarea_prop_arr, refarea_se_arr

def global_acc(df):

	ref_val = df['reference'].to_numpy()
	map_val = df['classification'].to_numpy()
	samp_weight = 1 / df['prob_amos'].to_numpy()
	
	mask_correct = (map_val == ref_val)
	map_correct = np.sum(np.where(mask_correct, 1, 0) * samp_weight)
	population = population_estimation(df)

	glob_acc = (map_correct / population)

	glob_acc = glob_acc
	glob_se = global_se(df, mask_correct, population)

	return glob_acc, glob_se

def user_prod_acc(df, class_values):

	user_acc_arr = []
	prod_acc_arr = []
	user_se_arr = []
	prod_se_arr = []

	ref_val = df['reference'].to_numpy()
	map_val = df['classification'].to_numpy()
	samp_weight = 1 / df['prob_amos'].to_numpy()

	for class_val in class_values:

		map_total = np.sum(np.where((map_val == class_val), 1, 0) * samp_weight)
		map_correct = np.sum(np.where(np.logical_and((map_val == class_val),(map_val == ref_val)), 1, 0) * samp_weight)

		ref_total = np.sum(np.where((ref_val == class_val), 1, 0) * samp_weight)
		ref_correct = np.sum(np.where(np.logical_and((ref_val == class_val),(map_val == ref_val)), 1, 0) * samp_weight)

		user_acc = 0
		if map_total > 0:
			user_acc = map_correct / map_total

		prod_acc = 0
		if ref_total > 0:
			prod_acc = ref_correct / ref_total

		user_se, prod_se = user_prod_se(df, class_val, user_acc, prod_acc, map_total, ref_total)

		user_acc_arr.append(user_acc)
		prod_acc_arr.append(prod_acc)
		user_se_arr.append(user_se)
		prod_se_arr.append(prod_se)

	return user_acc_arr, prod_acc_arr, user_se_arr, prod_se_arr

def config_class_21(df):
	agro_filter = (df['classification'] == 21) & (df['reference'].isin([15,19,20]))
	df.loc[agro_filter, 'reference'] = 21

	return df

# gruposBandas = [1,2,3,6]
gruposBandas = [1]

for reg in range(1):
	print('region # {}'.format(reg))

	for gb in gruposBandas:

		print("grupos de bandas G{}".format(gb))

		nomeTempCSV = 'MatrixC_reg_' + str(reg) + '_GB_bandasG' + str(gb) + '.csv'
		
		print("carregando tabela {}".format(nomeTempCSV))

		df = read_csvs(nomeTempCSV)

		total_points = population_estimation(df)


# df = df[df['POINTEDITE'] == '-']
# df = config_class_21(df)

# # regions = df['BIOMA'].unique().tolist()

# regions = ['CAATINGA']
# #regions.append('BRASIL')
# print("lista de regions",regions )
# for region in regions:
# 	accuracy_assessment_all(df, region)