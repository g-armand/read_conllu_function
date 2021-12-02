import conllu_io
"""
Make sure to import this function in your main program by writing "import read_conllu_function" at the top.
Make sure to save conllu_io.py in the same repository as this one.
"""

#This function will use the read_conllu function from conllu_io.py. 
def get_train_corpus(train_corpus):
	"""
	train_corpus: a .conllu file, in this situation from a universal dependencies project.
	returns a dictionnary with words from the corpus as keys and a list of associated tags as values.
	"""
	train_list = list()
	dico = dict()

	#conllu_io.read_conllu returns a generator object, so we need to iterate through the whole corpus,
	#we store the word and the associated tag in a tuple: temp, it is then appended to the train_list list.
	for elt in conllu_io.read_conllu(train_corpus):
		temp = (elt[1], elt[2]["cpos"]) #we retrieve words(a list: elt[1]) and tags(a list: elt[2]["cpos"])
		train_list.append(temp)

	#iteration over the lis of tuples
	for index in range(len(train_list)):
		#unpacking of word and associated tag, (not considering first and last element since they are just flags for start and end of sentence)
		for word, tag in zip(train_list[index][0][1:-1], train_list[index][1][1:-1]):

			#it is necessary to handle exceptions here because encoding latin1 cannot convert the ligature of 'o' and 'e' found in "coeur"
			try:
				#it is necessary to encode in "latin1" and then decode it in "utf-8"
				clean_word = word.encode("latin1").decode("utf-8")

				#if the encoding decoding phasis has gone well, we append the tag to the corresponding word in the dictionnary
				if clean_word in dico.keys() and tag not in dico[clean_word]:
					dico[clean_word].append(tag)
				#... or we create the couple in the dictionnary
				else:
					dico[clean_word] = [tag]
			#in case we encounter a not encodable character, we just not consider it, for now it's fine...
			except UnicodeEncodeError:
				pass



	return dico

print(get_train_corpus("test_gsd.conllu"))