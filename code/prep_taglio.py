import re
import glob
import os
from datetime import date

VERSION_NUMBER = 9

# CHANGELOG
#   v2: '(UIO,X,Y,Z)' era precedente inserito ad ogni cambio di utensile, invece che solo in quello iniziale
#       Aggiunto supporto per '(TCP)' e '(TCP,1)' senza cambio utensile
#   v4: Riconosce 'R2'/'r2' e 'R9'/'r9' nel nome del file ed esporta le modifiche necessarie
#       Riconosce qualsiasi estensione, non solo .nc
#       Cambiato l'header
#   v5: Riconosce 'INIZIO LINK' e 'FINE LINK' e lascia solo una riga tra i due; (se una Z viene trovata dopo un 'INIZIO LINK' e prima di un 'FINE LINK', esporta tutte le righe senza modifiche)
#   v6: Riconosce 'R3'/'r3' nel nome del file ed esporta le modifiche necessarie
#   v7: Riconosce 'R6'/'r6' nel nome del file ed esporta le modifiche necessarie
#   v8: Aggiunte spaziature (dopo 'Nxx' e tra le coordinate)
#       Fix: riconosce 'F2.5'
#   v9: Nuovo header
#       Rimossi comandi 'DIS'
#       Esportazione data
#       Riconosce 'CLIENTE', 'TAGLIO PEZZO', 'NOTE', 'DESCRIZIONE PEZZO' e legge i relativi dati che seguono
#       Separazione visiva cambio utensile
#       Carriage return dopo il prompt per la sovrascrittura
#       Riconosce 'revXX'/'rev_XX'/'rev.XX' nel nome del programma
#
#
# PLANNED:
#   Data nell'header
#   R4, R5
#   Posizioni dime
#   Input nome?
#   Centratura utensili in header
#   Numerazione righe

MOTORE_UTENSILE  = 0
MOTORE_LUNGHEZZA = 1

CLIENT_SEARCH_TOKEN       = 'CLIENTE'
DESC_SEARCH_TOKEN         = 'DESCRIZIONE PEZZO'
CODE_SEARCH_TOKEN         = 'TAGLIO PEZZO'
PROGRAM_NAME_SEARCH_TOKEN = 'NOTE'

desc_first_line_max_length = 34
desc_other_line_max_length = 45
robot_console_line_size    = 80

info_text_blank = '''
;
;
;
;
'''[1:]

info_text = '''
;                             * * * __NOMEPR__ * * *
; ==============================================================================
;                                                "__CLIENTE__"
; __PRIMARIGADESCRIZIONE__             [__CODICE__] __REV____ALTRERIGHEDESCRIZIONE__
;
; ==============================================================================
; __UTENSILI__
;  <R__NROBOT__>  __DIMA__
;                                      __REV__  __DATA__ __PROGRAMMATORE__
;
; ==============================================================================
'''[1:]

origin_text = '''
G79 G0 Z0
G79 G0 Y-100
;
(UIO,X,Y,Z)
;
'''[1:]

start_text = '''
;
M2__NMOTORE__ S19000
;
__ORIGIN__; ================================== M__NMOTORE__ __UTENSILE__ =====================================
G90 G0 __X__ __Y__ __B__ __A__
;
L365=0
L385=__LUTENSILE__ ; L. ut. Libera
L386=__NMOTORE__ ; Numero Motore
;
(TCP,1)
;
G90 G0 __X__ __Y__
;
'''[1:]

end_text = '''
;
(TCP)
;
(UAO,0)
;
G90 G0 Z0
G90 G0 Y-100
;
A0 B0
;
X0 Y0 Z0
;
M5
;
'''[1:]

def str_replace_at_index(s, index, replacement):
	l = list(s)
	l[index] = replacement
	return "".join(l)

def str_get_value(s, identifier, separator = ':', end_token = '\n'):
	value_start_index = s.find(identifier)
	value_text = ''
	if value_start_index > 0:
		value_start_index = s.find(separator, value_start_index + len(identifier)) + len(separator)
		value_end_index = value_start_index

		if isinstance(end_token, list) or isinstance(end_token, tuple):
			min_index = s.find(end_token[0], value_start_index)
			for token in end_token[1:]:
				index = s.find(token, value_start_index)
				if index > 0 and index < min_index:
					min_index = index
			value_end_index = min_index
		else:
			value_end_index = s.find(end_token, value_start_index)
		value_text = s[value_start_index : value_end_index].strip()
	return value_text

def process(name):
	robot_number = 0
	nome_programma     = '_NOMEPR_'
	nome_programmatore = 'programmatore'
	descrizione_pezzo  = '_descrizione_'
	codice_pezzo       = '_codice_'
	client_text        = '_cliente_'
	rev_text           = '     '
	dima               = 'XX'


	info_inserted    = False
	is_writing       = False
	tcp1_found       = False
	tcp0_found       = False
	g0_found         = False
	origin_inserted  = False
	is_changing_tool = False
	tcp_without_toolchange_buffer = ''
	is_linking       = False
	link_buffer      = ''

	motori      = [None, None, None]
	current_mot = ''
	current_len = ''

	re_g0_coordinate_x = re.compile('X-?[0-9]+\.?[0-9]*')
	re_g0_coordinate_y = re.compile('Y-?[0-9]+\.?[0-9]*')
	re_g0_coordinate_z = re.compile('Z-?[0-9]+\.?[0-9]*')
	re_g0_coordinate_a = re.compile('A-?[0-9]+\.?[0-9]*')
	re_g0_coordinate_b = re.compile('B-?[0-9]+\.?[0-9]*')
	re_l385			   = re.compile('=[0-9]+\.?[0-9]*')
	re_l386 		   = re.compile('=[0-9]+')
	re_dis             = re.compile('DIS,".*"')
	re_n               = re.compile('N[0-9]+')
	re_XYZAB           = re.compile('[0-9][XYZAB][0-9]+')

	if ('r2' in name.lower()):
		robot_number = 2
	elif ('r3' in name.lower()):
		robot_number = 3
	elif ('r6' in name.lower()):
		robot_number = 6
	elif ('r9' in name.lower()):
		robot_number = 9

	with open('in/' + name,'r') as fin:
		should_overwrite = True
		prompt_text = ''
		if os.path.exists('out/' + name):
			prompt_text = "Il file '" + name + "' esiste nella cartella 'out', sovrascrivere? [Sn] "
			choice = input(prompt_text)
			should_overwrite = ((choice) and (choice[0].lower() == 's'))
			prompt_length = len(prompt_text)
			if choice:
				prompt_length += len(choice)
			print('\033[1A\r' + ' ' * prompt_length + '\r', end='')
			#print('\b' * prompt_length, end='')
		if should_overwrite:
			with open('out/' + name, 'w') as fout:
				# ricerca utensili
				fin_content = fin.read()

				#
				# Ricera utensili utilizzati
				# ================================================================================================
				match_index = fin_content.find('FRESA')
				utensile = ''
				while (match_index > 0):
					line = fin_content[match_index:].split('\n')[0]
					if 'CILINDRICA' in line:  # FRESA
						utensile = 'F'
					elif 'SFERICA' in line:   # DISCO
						utensile = 'D'
					ut_start = line.find('D=') + 2
					ut_end   = line.find('.', ut_start)
					utensile += line[ut_start:ut_end]
					if (line[ut_end:ut_end+3] != '.00'):
						utensile += line[ut_end:ut_end+2]

					l385_index = fin_content.find('L385=',match_index) + 5
					l386_index = fin_content.find('L386=',match_index) + 5
					n_motore = int(fin_content[l386_index:l386_index+1]) - 2
					len_ut   = fin_content[l385_index:l385_index+2]
					if (n_motore < 0) or (n_motore > 2):
						___ERRORE_N_MOTORE_NON_VALIDO
					elif (motori[n_motore] != None) and ((motori[n_motore][MOTORE_UTENSILE][0] != utensile[0]) or (motori[n_motore][MOTORE_LUNGHEZZA] != len_ut)):
						___ERRORE_N_MOTORE_DUPLICATO

					motori[n_motore] = [None, None]
					motori[n_motore][MOTORE_UTENSILE]  = utensile
					motori[n_motore][MOTORE_LUNGHEZZA] = len_ut

					match_index = fin_content.find('FRESA', l386_index)

				#
				# Testo info: utensili
				# ================================================================================================
				utensili_text = ''
				for i in range(3):
					if motori[i] != None:
						utensili_text += 'M{} {} L{} - '.format(i+2, motori[i][0], motori[i][1])
				utensili_text = utensili_text[:-3]

				#
				# Testo info: robot
				# ================================================================================================
				robot_text = ''
				if (robot_number > 0):
					robot_text = ' [R' + str(robot_number) + ']'
				print(name, robot_text + ' (' + utensili_text + ')\n')

				#
				# Testo info: cliente
				# ================================================================================================
				client_search = str_get_value(fin_content, CLIENT_SEARCH_TOKEN)
				if client_search:
					client_text = client_search.lower()

				#
				# Testo info: descrizione
				# ================================================================================================
				desc_search = str_get_value(fin_content, DESC_SEARCH_TOKEN)
				if desc_search:
					descrizione_pezzo = desc_search.capitalize()

				#
				# Testo info: codice
				# ================================================================================================
				code_search = str_get_value(fin_content, CODE_SEARCH_TOKEN, ' ', [' ', '_'])
				if code_search:
					codice_pezzo = code_search.upper()

				#
				# Testo info: revisione
				# ================================================================================================
				REV_SEARCH_TOKEN = 'REV'
				rev_search = fin_content.find(REV_SEARCH_TOKEN)
				rev_value = ''
				if rev_search >= 0:
					rev_search += len(REV_SEARCH_TOKEN)

					# getting next alphanumeric
					is_numeric = False
					is_started = False
					for c in fin_content[rev_search:]:
						if is_started:
							if is_numeric:
								if c.isnumeric():
									rev_value += c
								else:
									rev_value = str(int(rev_value))
									break
							else:
								if c.isalpha():
									rev_value += c
								else:
									break
						else:
							if c.isalpha():
								is_numeric = False
								is_started = True
								rev_value += c
							elif c.isnumeric():
								is_numeric = True
								is_started = True
								rev_value += c
					rev_text = 'Rev.' + rev_value

				#
				# Testo info: nome programma
				# ================================================================================================
				name_search = str_get_value(fin_content, PROGRAM_NAME_SEARCH_TOKEN, ' ', '\n')
				if name_search:
					nome_programma = name_search.upper()

				for line in fin_content.split('\n'):
					line_number = re_n.findall(line)[0]
					line = line.replace(line_number, line_number + '  ')
					XYZAB_search = re_XYZAB.search(line)
					while XYZAB_search != None:
						span = XYZAB_search.span()
						coordinate_string = line[span[0] + 1:span[1]]
						line = line.replace(coordinate_string, ' ' + coordinate_string)
						XYZAB_search = re_XYZAB.search(line)
					line += '\n'
					if not info_inserted:
						if 'DIS' in line:       # Info iniziale
							#
							# Formattazione descrizione
							# ================================================================================================
							if len(descrizione_pezzo) <= desc_first_line_max_length:
								descrizione_pezzo = [descrizione_pezzo]
							else: # len_desc > desc_first_line_max_length
								max_len = desc_first_line_max_length
								processed_len = 0
								while (len(descrizione_pezzo) - processed_len) > max_len:
									last_space_index = descrizione_pezzo.rfind(' ', processed_len, processed_len + max_len)
									if last_space_index < 0:
										last_space_index = descrizione_pezzo.find(' ', processed_len + max_len)

									if last_space_index > 0:
										descrizione_pezzo = str_replace_at_index(descrizione_pezzo, last_space_index, '\n; ')
										processed_len = last_space_index + 3
									else:
										break
									max_len = desc_other_line_max_length
								descrizione_pezzo = descrizione_pezzo.split('\n')

							descrizione_pezzo[0] = descrizione_pezzo[0].ljust(desc_first_line_max_length, ' ')

							#
							# Formattazione data
							# ================================================================================================
							date_text = date.today().strftime('%d/%m/%Y')

							#
							# Output intestazione
							# ================================================================================================
							prima_riga_desc  = descrizione_pezzo[0]
							altre_righe_desc = ''
							if len(descrizione_pezzo) > 1:
								descrizione_pezzo[1] = '\n' + descrizione_pezzo[1]
								altre_righe_desc = descrizione_pezzo[1:]
							fout.write(info_text.\
									   replace('__NOMEPR__', nome_programma).\
									   replace('__UTENSILI__', utensili_text.center(robot_console_line_size-2, ' ').rstrip()).\
									   replace('__DIMA__', dima).\
									   replace('__NROBOT__', str(robot_number).replace('0','X')).\
									   replace('__PROGRAMMATORE__', nome_programmatore).\
									   replace('__PRIMARIGADESCRIZIONE__', prima_riga_desc).\
									   replace('__ALTRERIGHEDESCRIZIONE__', '\n'.join(altre_righe_desc)).\
									   replace('__CODICE__', codice_pezzo).\
									   replace('__CLIENTE__', client_text).\
									   replace('__DATA__', date_text).\
									   replace('__REV__', rev_text))
							info_inserted = True
							tcp0_found = True
					else:  # info_inserted == True
						line = line.replace('G00', 'G0')
						line = line.replace('G01', 'G1')
						if tcp0_found and (not tcp1_found):
							is_writing = False

							if 'L385' in line:
								# TODO: use this for info_text
								current_len = re_l385.findall(line)[0][1:]
								is_changing_tool = True
							elif 'L386' in line:
								current_mot = re_l386.findall(line)[0][1:]
							elif '(TCP' in line:
								tcp1_found = True
								tcp0_found = False

								if not is_changing_tool:
									fout.write(tcp_without_toolchange_buffer + line)

							tcp_without_toolchange_buffer += line
						elif tcp1_found:  # tcp1_found == True
							if is_changing_tool:
								if (not g0_found) and ('G0' in line):
									x = re_g0_coordinate_x.findall(line)[0]
									y = re_g0_coordinate_y.findall(line)[0]
									z = re_g0_coordinate_z.findall(line)[0]
									a = re_g0_coordinate_a.findall(line)[0]
									b = re_g0_coordinate_b.findall(line)[0]

									if origin_inserted:
										origin = ''
									else:
										origin = origin_text
										origin_inserted = True

									mot_index      = int(current_mot)
									utensile_text  = ''
									if (mot_index > 1) and (mot_index <= 4):
										utensile_text = motori[mot_index-2][MOTORE_UTENSILE]

									fout.write(start_text.\
												replace('__ORIGIN__',    origin).\
												replace('__NMOTORE__',   current_mot).\
												replace('__UTENSILE__',  utensile_text).\
												replace('__LUTENSILE__', current_len).\
												replace('__X__', x).\
												replace('__Y__', y).\
												replace('__Z__', z).\
												replace('__A__', a).\
												replace('__B__', b))
									line = ''
								is_changing_tool = False
							is_writing = True
							tcp1_found = False
							tcp_without_toolchange_buffer = ''
						else:   #tcp0_found == False and tcp1_found = False
							if is_linking:
								if 'Z' in line:
									is_linking = False
									is_writing = True
									line = link_buffer + line
									link_buffer = ''
								if 'FINE LINK' in line:
									is_linking = False
									is_writing = True
									link_buffer = link_buffer.split('\n')
									line = link_buffer[len(link_buffer) - 2] + '\n' + line
									link_buffer = ''
							else:
								if 'INIZIO LINK' in line:
									is_linking = True
									is_writing = False
									fout.write(line)
								if 'FINE PROGRAMMA' in line:
									fout.write(end_text)
									break
								if '(TCP)' in line:
									tcp0_found = True

					if is_writing:	
						fout.write(line)
					elif is_linking:
						if not ('INIZIO LINK' in line):
							link_buffer += line
			if robot_number > 0:
				os.rename('out/' + name, 'out/temp')
				if robot_number == 2:
					process_r2_r9(name, False)
				elif robot_number == 3:
					process_r3(name)
				elif robot_number == 6:
					process_r6(name)
				elif robot_number == 9:
					process_r2_r9(name, True)
				os.remove('out/temp')

def process_r6(name):
	uao0_inserted = False

	with open('out/temp','r') as fin:
		should_overwrite = True
		if os.path.exists('out/' + name):
			prompt_text = "Il file '" + name + "' esiste nella cartella 'out', sovrascrivere? [Sn] "
			choice = input("\n" + prompt_text)
			should_overwrite = choice[0].lower() == 's'
		if should_overwrite:
			with open('out/' + name, 'w') as fout:
				for line in fin.readlines():
					if not uao0_inserted:
						if '(UAO,0)' in line:
							uao0_inserted = True
					else:
						line = line.replace('X0', 'X2550')
					fout.write(line)

def process_r2_r9(name, is_r9):
	lines_from_tcp0 = -1
	hold_buffer = ''
	h0_inserted = False

	with open('out/temp','r') as fin:
		should_overwrite = True
		if os.path.exists('out/' + name):
			choice = input("\nIl file '" + name + "' esiste nella cartella 'out', sovrascrivere? [Sn] ")
			should_overwrite = choice[0].lower() == 's'
		if should_overwrite:
			with open('out/' + name, 'w') as fout:
				for line in fin.readlines():
					if lines_from_tcp0 < 0:
						if h0_inserted and is_r9 and ('X0' in line):
							line = line.replace('X0', 'X2550')
						fout.write(line)
						if 'L386' in line:
							fout.write('M141\n')
						elif '(TCP)' in line:
							lines_from_tcp0 = 1
					elif lines_from_tcp0 == 1:
						hold_buffer += line
						lines_from_tcp0 = 2
					elif lines_from_tcp0 == 2:
						if '(UAO,0)' in line:
							hold_buffer += 'h0\n;\n'
							h0_inserted = True
						line = hold_buffer + line
						hold_buffer = ''
						lines_from_tcp0 = -1
						fout.write(line)

def process_r3(name):
	uio_found = False
	uao0_found = False

	with open('out/temp','r') as fin:
		should_overwrite = True
		if os.path.exists('out/' + name):
			choice = input("\nIl file '" + name + "' esiste nella cartella 'out', sovrascrivere? [Sn] ")
			should_overwrite = choice[0].lower() == 's'
		if should_overwrite:
			with open('out/' + name, 'w') as fout:
				for line in fin.readlines():
					if not uio_found:
						if 'UIO' in line:
							uio_found = True
						line = line.replace('G79 G0 Z0', 'G79 G0 Z200')
						if 'G79 G0 Y-100' in line:
							line = ''
					elif uao0_found:
						line = line.replace('G90 G0 Z0', 'G90 G0 Z200')
						line = line.replace('A0 B0', 'G90 G0 Y310 A-90 B0')
						line = line.replace('X0 Y0 Z0', 'X-1252 Y322 Z200 A-135 B0')
						if 'G90 G0 Y-100' in line:
							line = ''
					elif '(UAO,0)' in line:
						uao0_found = True
					fout.write(line)

if __name__ == '__main__':
	paths = glob.glob('in/*')
	if not os.path.exists('out'):
	    os.makedirs('out')

	print("PREPARAZIONE TAGLIO (v{})\n".format(VERSION_NUMBER))
	for path in paths:
		if not os.path.isdir(path):
			filename = os.path.basename(path)
			if not ('maschera' in filename.lower()):
				process(filename)
	
	input("\n\nPremere invio per chiudere...")

