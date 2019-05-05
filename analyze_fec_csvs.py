from pprint import pprint
import json
import time
import os
import glob

import pandas as pd


candidates = ["romney", "obama", "mccain", "trump", "clinton"]

candidate_data = {}

def main():
	csv_names = get_csvs()

	year_maxes = {"08": 2300,
			"12": 2500,
			"16": 2700}

	# fills in candidate_data dict
	for name in csv_names:
		analyze_csv(str(name), year_maxes)

	# combines candidate data dict into sometihng usable, while accounting for double-max donations
	for cand in candidate_data:
		this_cand = candidate_data[cand]
		try:
			this_cand['primary_max_donors_count'] = this_cand['positivemax_primary'] - this_cand['positivedbl_general'] + this_cand['positivedbl_primary'] - this_cand['negatives_dbl_primary']
			this_cand['general_max_donors_count'] = this_cand['positivemax_general'] - this_cand['positivedbl_primary'] + this_cand['positivedbl_general'] - this_cand['negatives_dbl_general']
			this_cand['total_max_donors_count'] = this_cand['general_max_donors_count'] + this_cand['primary_max_donors_count']
		except:
			pass

	pprint(candidate_data)

	write_data_json(candidate_data, "candidate_data")
	write_clean_data_csv(candidate_data, "candidate_data", ['primary_max_donors_count', 'general_max_donors_count'])

	


def get_csvs():
	path = 'data/'
	extension = 'csv'
	os.chdir(path)
	result = glob.glob('*.{}'.format(extension))
	return result

def analyze_csv(csv_path, year_maxes):
	orig_df = pd.read_csv(csv_path)

	# filter to just indv contributions
	is_indv_df = orig_df[orig_df["is_individual"] == "t"]


	# parse out the candidate name and year
	this_candidate = ""
	this_year = ""

	for cand in candidates:
		if cand in csv_path:
			this_candidate = cand
			this_year = csv_path.replace(cand, "")[0:2]

	unique_cand = this_candidate + this_year


	# count the contributions of each type
	d = {}
	if 'negative' in csv_path:
		d['negatives_primary'] = count_negatives(this_year, is_indv_df, 'primary', year_maxes)
		d['negatives_general'] = count_negatives(this_year, is_indv_df, 'general', year_maxes)
		d['negatives_dbl_primary'] = count_negatives_dbl(this_year, is_indv_df, 'primary', year_maxes)
		d['negatives_dbl_general'] = count_negatives_dbl(this_year, is_indv_df, 'general', year_maxes)
	elif 'positive' in csv_path:
		d['positivemax_primary'] = count_positivemax(this_year, is_indv_df, 'primary', year_maxes)
		d['positivemax_general'] = count_positivemax(this_year, is_indv_df, 'general', year_maxes)
		d['positivedbl_primary']  = count_positivedbl(this_year, is_indv_df, 'primary', year_maxes)
		d['positivedbl_general']  = count_positivedbl(this_year, is_indv_df, 'general', year_maxes)
		d['positivedbl_none']  = count_positivedbl(this_year, is_indv_df, '', year_maxes)


	if unique_cand not in candidate_data:
		candidate_data[unique_cand] = d
	else:
		for key in d:
			if key in candidate_data[unique_cand]:
				candidate_data[unique_cand][key] = candidate_data[unique_cand][key] + d[key]
			else:
				candidate_data[unique_cand][key] = d[key]




def count_negatives(this_year, df, election_type, year_maxes):
	neg_maxes = df[df['contribution_receipt_amount'] == (-1 * year_maxes[this_year])]
	neg_maxes = neg_maxes[neg_maxes['fec_election_type_desc'] == election_type.upper()]
	return len(neg_maxes)

def count_negatives_dbl(this_year, df, election_type, year_maxes):
	neg_maxes = df[df['contribution_receipt_amount'] == (-2 * year_maxes[this_year])]
	neg_maxes = neg_maxes[neg_maxes['fec_election_type_desc'] == election_type.upper()]
	return len(neg_maxes)

def count_positivemax(this_year, df, election_type, year_maxes):
	pos_maxes = df[df['fec_election_type_desc'] == election_type.upper()] 
	pos_maxes = pos_maxes[pos_maxes['contribution_receipt_amount'] == year_maxes[this_year]] 
	return len(pos_maxes)

def count_positivedbl(this_year, df, election_type, year_maxes):
	posdbl_maxes = df[df['contribution_receipt_amount'] == (year_maxes[this_year]*2)] 
	posdbl_maxes = posdbl_maxes[posdbl_maxes['fec_election_type_desc'] == election_type.upper()] 
	return len(posdbl_maxes)







def write_data_json(content, filename):
	with open('output/' + filename + '.json', "w") as ofile:
		ofile.write(json.dumps(content))
	ofile.close()

def write_clean_data_csv(content, filename, keepkeys):
	data = []
	for key in content:
		d = {}
		d['campaign'] = key
		for key2 in content[key]:
			if key2 in keepkeys:
				d[key2] = content[key][key2]
		data.append(d)

	pd.DataFrame(data).to_csv('output/' + filename + '.csv', index=0)



if __name__ == "__main__":
	main()