
"""
Make sure to import this function in your main program by writing "import read_conllu_function" at the top.
Make sure to save conllu_io.py in the same repository as this one.
"""

def get_train_corpus(corp = "train_gsd.conllu"):
	
	dico = {}
	with open(corp, "r", encoding="latin1") as file:

		for line in file:



			#it is necessary to handle exceptions here because encoding latin1 cannot convert the ligature of 'o' and 'e' found in "coeur"
			try:

				#it is necessary to encode in "latin1" and then decode it in "utf-8"
				line = line.encode("latin1").decode("utf-8")
						#in case we encounter a not encodable character, we just not consider it, for now it's fine...
			except (UnicodeDecodeError, UnicodeEncodeError) as e:
				continue
			#lines of length <= 1 are the ones between two sentences, and the ones beginning with '#' are the one at the beggining of each sentence	 
			if len(line) <= 1 or line[0] == "#":
				continue
			line= line.split("	")
			clean_word = line[1]
			tag = line[3]

			#if the encoding decoding phasis has gone well, we append the tag to the corresponding word in the dictionnary
			if clean_word in dico.keys() and tag not in dico[clean_word]:
				dico[clean_word].append(tag)
			#... or we create the couple in the dictionnary
			else:
				dico[clean_word] = [tag]
	return dico

