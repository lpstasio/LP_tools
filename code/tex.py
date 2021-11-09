# TEXporter
_VERSION = 9

from tex_defaults import *

# CHANGELOG
#   v0: Riconosce le diverse sezioni di cui è composto il programma.
#        Per 'sezione' si intende una parte di programma che va da un'attivazione del tcp alla successiva disattivazione;
#        ogni sezione è caratterizzata da un motore, un utensile e una lunghezza utensile
#   v1: Configurabile
#       Ottimizzazione link
#       Spaziatura coordinate
#       Padding numeri righe
#       Posizioni dima configurabili
#   v2: UX migliorata
#   v3: Supporto maschere
#   v4: Aggiunti tempalte di default pre-inclusi
#       Controllo Z per programmi maschere
#       Controllo numero utensili per programmi maschere
#   v5: "Attenzione:" e "Errore:"
#   v6: Quasi tutte le informazioni sul programma sono lette dal nome dell'nc
#   v7: Codice Lapi
#   v8: Aggiunte sostituzioni per i programmi di taglio maschere
#   v9: Fixati link col tcp off
#
# PLANNED
#     add C axis support
#     allow empty variables
#     rename file?
#     preload all templates and variables (and report errors)
#
#
#
#
#
# variabili configurazione:
#            "stringa_cliente"               : "CLIENTE",
#            "stringa_descrizione_pezzo"     : "DESCRIZIONE PEZZO",
#            "stringa_codice"                : "CODICE PEZZO",
#            "stringa_revisione"             : "REV",
#            "stringa_nome_programma"        : "NOTE"
#            "desc_max_lunghezza"            : "34",
#            "formato_data"                  : "g.m.aaaa",
#
#            righe_numerate:                 1
#            numerazione_righe_sulla_destra: 1
#            distanza_numeri_righe:          70
#            mantieni_prima_coordinata:      0
#            ottimizza_link:                 1
#            sostituisci_g00_g01:            1
#            numero_spazi_tra_coordinate:    2

import os, glob, keyboard
from datetime import datetime


WARNING_INTRODUCTION = ' [Attenzione: '
templates_not_found = []

def report_warning(ui_text, warning, filename = ''):
	if ui_text:
		ui_text += '\n'
	pass

	print(ui_text,end='')
	if filename:
		filename = " nel file '{}'".format(filename)
	print('   → Attenzione{}: '.format(filename) + warning)
pass

def report_error(ui_text, error, filename = ''):
	print(ui_text)
	if filename:
		filename = " nel file '{}'".format(filename)
	print('   → Errore{}: '.format(filename) + error)
pass


def report_error_and_exit(ui_text, error, filename = ''):
	report_error(ui_text, error, filename)

	print("\n\nPremere invio per chiudere...", end='')
	while True:
		event = keyboard.read_event()
		if (event.name == 'enter') and (event.event_type == 'up'):
			break
		pass
	pass
	exit() # @todo: maybe just skip current program?
pass

def ui_warn(warning_text, warning):
	if not warning_text:
		warning_text += ' [Attenzione: '
	pass
	warning_text += warning + '; '

	return warning_text
pass

def str_insert(s, insert, index):
	return insert.join([s[:index], s[index:]])
pass

def str_replace_at_index(s, index, replacement):
	l = list(s)
	l[index] = replacement
	return "".join(l)
pass

def _str_get_number(s, ignore_before):
	result = ''
	for c in s:
		if (c.isdecimal()) or \
			((not result) and (c == '-')) or \
			(    (result) and (c == '.') and ('.' not in result)):
			result += c
		elif ignore_before:
			if result:
				break
		else:
			break
		pass
	pass
	return result
pass


def str_get_number_ignore_any_before(s):
	result = _str_get_number(s, True)
	return result
pass


def str_get_number_or_nothing(s):
	return _str_get_number(s, False)
pass


def str_get_coordinate(axis, line):
	result = ''
	if (axis in 'XYZABC'):
		search_index = line.find(axis)
		if search_index >= 0:
			result = str_get_number_ignore_any_before(line[search_index:])
			if not result:
				result = '0'
			pass
		else:
			result = 'INESISTENTE'
		pass
	else:
		print("Asserzione fallita: asse '{}' invalido".format(axis))
		__ASSERT_UNDEFINED_AXIS
	pass
	return result
pass


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
		pass
		value_text = s[value_start_index : value_end_index].strip()
	pass
	return value_text
pass


def in_str(s, subst):
	if (not isinstance(subst, list)) and (not isinstance(subst, tuple)):
		subst = [subst] 
	pass

	for token in subst:
		if token in s:
			return True
	pass

	return False
pass


def read_template_raw(filename, robot=0, maschera_type=MASCHERA_NOMASCHERA):
	template  = ''
	variables = []

	path = 'config/' + filename
	if maschera_type != MASCHERA_NOMASCHERA:
		path = 'config/maschere/{}/{}'.format(maschera_type, filename)
		if not os.path.exists(path):
			path = 'config/maschere/' + filename
		pass
	elif robot > 0:
		path = 'config/r{}/{}'.format(robot, filename)
		if not os.path.exists(path):
			path = 'config/' + filename
		pass
	pass

	if not os.path.exists(path):
		if path not in templates_not_found:
			report_warning('', "template '{}' non trovato!".format(path))
			templates_not_found.append(path)
		pass
		template = default_templates[path]
	else:
		with open(path, 'r') as file:
			template = file.read()
		pass
	pass

	if template:
		mark_count = template.count('$')
		if (mark_count % 2):
			report_error_and_exit('', "Numero dispari di '$'", path)
		pass

		mark_start = template.find('$')
		while mark_start >= 0:
			mark_end = template.find('$', mark_start+1)
			var_name = template[mark_start+1 : mark_end]
			if (not var_name) or (var_name.isspace()):
				report_error_and_exit('', "Due '$' si seguono senza racchiudere il nome di una variabile", path)
			pass

			if not (var_name in variables):
				variables.append(var_name)
			pass
			mark_start = template.find('$', mark_end+1)
		pass
	pass

	return template, variables, path
pass


def read_and_process_template(filename, variable_database, repeating_vars):
	maschera_type = variable_database.get('MASCHERA_TYPE', MASCHERA_NOMASCHERA)
	robot         = variable_database.get('ROBOT', '0')
	if not robot:  # if robot == ''
		robot = '0'
	robot = int(robot)

	template, pending_vars, path = read_template_raw(filename, robot, maschera_type)
	for var in pending_vars:
		if ':' in var:                                      # file references
			var_segments = var.split(':')
			if len(var_segments) > 2:
				report_error_and_exit('', "sintassi errata '${}$'".format(var), path)
			pass

			repeat_count    = var_segments[0]
			referenced_file = var_segments[1]
			if referenced_file == filename:
				report_error_and_exit('', "un template non può includere se stesso ('${}$)'".format(var), path)
			pass

			referenced_template = ''
			if repeat_count:
				repeat_count = int(repeat_count)
				if referenced_file not in repeating_vars.keys():
					repeating_vars[referenced_file] = repeat_count
				pass
				if(repeating_vars[referenced_file]):
					referenced_template = read_and_process_template(referenced_file, variable_database, repeating_vars)
					repeating_vars[referenced_file] -= 1
				pass
			else:
				referenced_template = read_and_process_template(referenced_file, variable_database, repeating_vars)
			pass

			template = template.replace('$'+var+'$', referenced_template)
		elif var in variable_database.keys():               # variables
			template = template.replace('$'+var+'$', variable_database[var])
		pass
	pass
	return template
pass


def _parse_tex(filename):
	vars = dict()

	if os.path.exists('config/' + filename):
		with open('config/' + filename, 'r') as tfile:
			line_number = 0
			for line in tfile.read().splitlines():
				line_number += 1

				comment_start = line.find(';')
				if comment_start >= 0:
					line = line[:comment_start].strip()
				pass

				if line:
					separator_index = line.find(':')
					if separator_index < 0:
						report_error_and_exit('', "nessun ':' trovato nella riga {} ({})".format(line_number, line), 'config/' + filename)
						# @todo: check
					pass

					var_name  = line[:separator_index].replace(' ', '')
					var_value = line[separator_index + 1:].lstrip()
					
					if not var_name:
						report_error_and_exit('', "nome variabile mancante nella riga {} ({})".format(line_number, line), 'config/' + filename)
						# @todo: check
					pass
					
					if var_name in vars.keys():
						report_warning('', "ridefinizione di '{}' nella riga {}, manterrà il valore precedente".\
									   format(var_name, line_number), filename)
					else:
						vars[var_name] = var_value
					pass
				pass
			pass
		pass
	pass
	return vars
pass


def config_make_bool(src_path, config, name):
	if config[name].isnumeric():
		config[name] = bool(int(config[name]))
	else:
		report_error_and_exit('', "la variabile '{}' deve essere '0' o '1'", src_path)
		# @todo: check
	pass
pass

def config_make_int(src_path, config, name):
	if config[name].isnumeric() or (config[name][0] == '-' and config[name][1:].isnumeric()):
		config[name] = int(config[name])
	else:
		report_error_and_exit('', "la variabile '{}' deve avere un valore numerico", src_path)
		# @todo: check
	pass
pass


def load_config(is_maschera = False):
	#
	# Lettura configurazione
	# ================================================================================================
	config = dict()
	path = 'configurazione.tex'
	if is_maschera:
		path = 'maschere/' + path
	config = _parse_tex(path)

	for key in config.keys():
		if not key in default_config.keys():
			report_warning('', "Variabile di configurazione '{}' non riconosciuta; sarà ignorata".format(key), path)
		pass
	pass

	#
	# Inserimento valori default per variabili non specificate
	# ================================================================================================
	forced_config = default_config.copy()
	forced_config.update(config)
	config = forced_config

	#
	# Controllo tipi variabili
	# ================================================================================================
	config_make_bool(path, config, 'righe_numerate')
	config_make_bool(path, config, 'numerazione_righe_sulla_destra')
	config_make_bool(path, config, 'mantieni_prima_coordinata')
	config_make_bool(path, config, 'ottimizza_link')
	config_make_bool(path, config, 'sostituisci_g00_g01')

	config_make_int(path, config, 'distanza_numeri_righe')
	config_make_int(path, config, 'numero_spazi_tra_coordinate')
	config_make_int(path, config, 'descrizione_max_lunghezza')


	#
	# Formattazione data
	# ================================================================================================
	date_format = config['formato_data']
	date_format = date_format.\
				  replace('aaaa',  '%Y').\
				  replace(  'aa',  '%y').\
				  replace(   'm',  '%m').\
				  replace(   'g',  '%d').\
				  replace(   'h',  '%I').\
				  replace(   'H',  '%H').\
				  replace(   'M',  '%M').\
				  replace(   's',  '%S')
	config['formato_data'] = date_format

	#
	# Array separatori codice lapi
	# ================================================================================================
	config['separatore_codice_lapi'] = config['separatore_codice_lapi'].split(',')

	return config
pass


def _parse_vars(config, robot = 0):
	result = None

	#
	# Lettura variabili
	# ================================================================================================
	if robot == 0:
		result = _parse_tex('variabili.tex')
		result['DATA'] = datetime.now().strftime(config['formato_data'])

		#
		# Inserimento valori default per variabili non specificate
		# ================================================================================================
		forced_vars = default_vars.copy()
		forced_vars.update(result)
		result = forced_vars
	elif robot > 0:
		result = _parse_tex('r{}/variabili.tex'.format(robot))
	elif robot == -1:         # @todo?
		result = _parse_tex('maschere/variabili.tex')
	pass

	if len(result) == 0:
		result = None
	pass

	return result
pass

def load_all_vars(config):
	result = [None]

	result[0] = _parse_vars(config, 0)
	
	for path in glob.iglob('config/[Rr][0-9]*'):
		robot_str = os.path.basename(path)
		if robot_str.lower()[0] == 'r':
			robot_str = robot_str[1:]
			if robot_str.isnumeric():
				robot = int(robot_str)

				if len(result) <= robot:
					extension_length = robot - len(result) + 1
					result.extend([None] * extension_length)
				pass

				result[robot] = _parse_vars(config, robot)
			pass
		pass
	pass

	return result
pass

def _parse_origin(path, s):
	result = dict()

	for piece in s.split(')'):
		if piece:
			start = piece.find('(')
			if start < 0:
				report_error_and_exit('', "parentesi non aperta '{}'".format(s), path)
								# @todo: check
			pass

			piece = piece[start+1:]

			if ',' not in piece:
				result['default'] = piece
			else:
				piece = piece.split(',')
				result[piece[0].strip()] = piece[1].strip()
			pass
		pass
	pass
	if len(result) == 0:
		result = None
	pass
	return result
pass

def load_origins():
	result = []
	
	for path in glob.iglob('config/[Rr][0-9]*/origini.tex'):
		robot_str = os.path.basename(os.path.dirname(path))
		if robot_str.lower()[0] == 'r':
			robot_str = robot_str[1:]
			if robot_str.isnumeric():
				robot = int(robot_str)
				

				if len(result) <= robot:
					extension_length = robot - len(result) + 1
					result.extend([None] * extension_length)
				pass
				result[robot] = [None, None, None]

				current_axis  = -1
				axes_lines = ['', '', '']
				with open(path, 'r') as fin:
					content = fin.read()
					if 'X' in content:
						result[robot][X_INDEX] = dict()
					pass
					if 'Y' in content:
						result[robot][Y_INDEX] = dict()
					pass
					if 'Z' in content:
						result[robot][Z_INDEX] = ''
					pass

					lines = content.splitlines()
					for i in range(len(lines)):
						line = lines[i]

						comment_start = line.find(';')
						if comment_start >= 0:
							line = line[:comment_start].strip()
						pass

						colon = line.find(':')
						if colon >= 0:
							before_colon = line[:colon]
							line = line[colon+1:].strip()

							if 'X' in before_colon:
								current_axis = X_INDEX
							elif 'Y' in before_colon:
								current_axis = Y_INDEX
							elif 'Z' in before_colon:
								current_axis = Z_INDEX
							else:
								report_error_and_exit('', "nessun asse specificato nella riga {}".format(i), path)
								# @todo: check
							pass
						pass
						
						if line.strip():
							if current_axis < 0:
								report_error_and_exit('', "coordinate specificate prima di definire un asse (riga {})".format(i), path)
								# @todo: check
							pass

							axes_lines[current_axis] += line
						pass
					pass


					# PARSING COORDINATES
					result[robot][X_INDEX] = _parse_origin(path, axes_lines[X_INDEX])
					result[robot][Y_INDEX] = _parse_origin(path, axes_lines[Y_INDEX])
					result[robot][Z_INDEX] = _parse_origin(path, axes_lines[Z_INDEX])
					if result[robot] == [None, None, None]:
						result[robot] = None
					pass
				pass
			pass
		pass
	pass

	return result
pass


def load_program_info(filename, content, config, warning_text):
	result = dict()
	result['all_CODICI'] = []
	filename = filename.lower()

	if 'maschera' in filename:
		result['MASCHERA_TYPE'] = MASCHERA_NUMERI if 'numeri' in filename else MASCHERA_BASE
		if '15mm' in filename or '15 mm' in filename:
			result['MASCHERA_DEPTH'] = MASCHERA_15MM
		else:
			result['MASCHERA_DEPTH'] = MASCHERA_25MM
		pass
	pass

	#
	# Cliente
	# ================================================================================================
	search = str_get_value(content, config['stringa_cliente'])
	if search:
		result['CLIENTE'] = search.lower()

	#
	# Ricerca informazioni nel nome dell'nc
	# ================================================================================================
	search = filename.find('c_')

	search = 0
	token_indices = []
	token_ids = ['p_', 'r_', 'd_', 'n_']
	c_start = 0

	# ricerca 'c_' per codici
	while True:
		search = filename.find('c_', c_start)
		if search > -1:
			token_indices.append(search)
			c_start = search + 1
		else:
			break
		pass
	pass

	# ricerca p_/r_/d_ per nome programma/robot/descrizione pezzo
	for id in token_ids:
		search = filename.find(id)
		if search > -1:
			token_indices.append(search)
		pass
	pass

	# ricerca fine nome file
	search = filename.rfind('.')
	if search > -1:
		token_indices.append(search)
	else:
		token_indices.append(len(filename))
	pass

	token_indices.sort()
	for i in range(len(token_indices)-1):
		start = token_indices[i]
		end   = token_indices[i+1]
		token = filename[start:end]

		if token[0] == 'c':
			lapi_separator_list = config.get('separatore_codice_lapi',['@'])
			lapi_separator = ''
			for separator in lapi_separator_list:
				if separator in token:
					lapi_separator = separator
				pass
			pass

			token     = token[2:]
			rev_text  = ''
			lapi_text = ''

			search_rev  = token.find('rev')
			search_lapi = token.find(lapi_separator)
			if search_rev < search_lapi:       # @todo: i'm making this in a hurry, it's hacky code
				if search_lapi > -1:
					lapi_text = token[search_lapi + len(lapi_separator):]
					token     = token[:search_lapi]
				pass

				if search_rev > -1:
					rev_text = token[search_rev + 3:]
					token    = token[:search_rev]
				pass
			else:
				if search_rev > -1:
					rev_text = token[search_rev + 3:]
					token    = token[:search_rev]
				pass

				if search_lapi > -1:
					lapi_text = token[search_lapi + len(lapi_separator):]
					token     = token[:search_lapi]
				pass
			pass

			lapi = lapi_text.strip().upper()
			rev  =  rev_text.strip().upper()
			result['all_CODICI'].append((token.strip(), lapi, rev))

		#
		# Nome programma
		# ================================================================================================
		elif token[0] == 'p':
			token = token[2:]
			nome_programma = token.strip().upper()

			result['PROGRAMMA'] = nome_programma
			if (len(nome_programma) != 7) and (len(nome_programma) != 8):
				warning_text = ui_warn(warning_text, "Il nome '{}' è composto da {} caratteri".\
									   format(result['PROGRAMMA'], len(result['PROGRAMMA'])))
			pass

		#
		# Robot e posizione dima
		# ================================================================================================
		elif token[0] == 'r':
			token = token[2:]
			search = token.find('(')

			posizione_dima = ''
			if search > -1:
				posizione_dima = token[search:].rstrip(') ').lstrip('( ').upper()
				token = token[:search]
			pass

			# Parsing posizione dima
			if (posizione_dima) and (len(posizione_dima) == 2):
				letter = ''
				number = str_get_number_ignore_any_before(posizione_dima)
				if ((len(number)) > 1) and ('0' in number):
					letter = '0'
					number = posizione_dima.replace('0', '')
				elif number.isdigit():
					letter = posizione_dima.replace(number, '')
				pass

				if ((letter.isalpha()) or (letter == '0')) and number.isdigit():
					result['POSIZIONEDIMA'] = number + letter
				pass
			pass

			result['ROBOT'] = str_get_number_or_nothing(token.strip())

		#
		# Descrizione
		# ================================================================================================
		elif token[0] == 'd':
			token = token[2:]
			descrizione = token.strip().capitalize()
			desc_max_len = config.get('descrizione_max_lunghezza', 0)

			result['DESCRIZIONE'] = descrizione.ljust(desc_max_len)

		#
		# Nome programmatore
		# ================================================================================================
		elif token[0] == 'n':
			token = token[2:].strip()
			if token:
				result['PROGRAMMATORE'] = token
			pass
		pass
	pass

	return result, warning_text
pass

def process(filename, config, all_vars, origins, ui_padding, is_maschera):
	term_size = None

	try:
		term_size = os.get_terminal_size()
	except OSError:
		pass
	pass

	should_overwrite = True
	ui_text = ''

	warning_text = ''

	nc_sections = []
	program_Zs  = []
	in_content = None
	in_lines   = None
	line_number = 1
	if os.path.exists('out/' + filename):
		should_overwrite = None
		max_prompt_len = 70 if term_size == None else (term_size.columns - 3)

		prompt_text = "Il file '{}' esiste nella cartella 'out', sovrascrivere? [Sn] "
		if (len(prompt_text) - 2 + len(filename)) > max_prompt_len:
			delta = len(filename) - (max_prompt_len - len(prompt_text) + 2)
			prompt_text = prompt_text.format(filename[:-delta - 3] + '...')
		else:
			prompt_text = prompt_text.format(filename)
		pass

		print(prompt_text, end='', flush=True)

		while should_overwrite == None:
			event = keyboard.read_event()
			if event.event_type == 'up':
				if event.name.lower() == 's':
					should_overwrite = True
				elif event.name.lower() == 'n':
					should_overwrite = False
				pass
			pass
		pass

		prompt_length = len(prompt_text)
		print('\r' + ' '*prompt_length + '\r',end='')
	if should_overwrite:
		short_name = filename
		if len(short_name) > MAX_UI_FILENAME_LEN:
			short_name = short_name[:MAX_UI_FILENAME_LEN + 1]
		pass

		ui_text = short_name + ' '*(ui_padding - len(short_name) + 2)

		with open('in/' + filename,'r') as fin:
			in_content = fin.read()
			in_lines = in_content.splitlines()

			robot = -1
			local_vars, warning_text = load_program_info(filename, in_content, config, warning_text)
			if 'MASCHERA_TYPE' not in local_vars.keys():         # ui for taglio
				robot = local_vars.get('ROBOT', '')

				if not robot:
					robot = '0'
					ui_text += ' '*9                                                           ## ui prompt
				else:
					padding = 2 - len(robot)                                                   ## ui prompt
					ui_text += ' '*padding + '<R' + robot + '> '

					pos_dima = local_vars.get('POSIZIONEDIMA', '')
					if pos_dima:
						ui_text += pos_dima + ' '
					else:
						ui_text += ' '*3
					pass
				pass
				robot = int(robot)
			else:                                               # ui for maschere
				type  = local_vars['MASCHERA_TYPE']
				depth = local_vars['MASCHERA_DEPTH']
				if depth == MASCHERA_25MM:
					depth = ''
				else:
					depth = ' '*(1 + len(MASCHERA_NUMERI)-len(type)) + depth
				pass
				ui_text += '<' + type + depth + '>'
			pass

			forced_vars = all_vars[0].copy()
			if robot and (all_vars[robot]):
				forced_vars.update(all_vars[robot])
			pass
			forced_vars.update(local_vars)
			local_vars = forced_vars

			if ('POSIZIONEDIMA' in local_vars.keys()) and (local_vars['POSIZIONEDIMA'] != default_vars['POSIZIONEDIMA']):
				if (robot >= 0) and (len(origins) != 0) and (robot < (len(origins) + 1)) and (origins[robot]):
					pos = local_vars['POSIZIONEDIMA']
					number = pos[0]
					letter = pos[1]

					if origins[robot][Z_INDEX]:
						local_vars['ORIGZ'] = origins[robot][Z_INDEX]['default']
					pass

					if origins[robot][X_INDEX]:
						if letter in origins[robot][X_INDEX].keys():
							local_vars['ORIGX'] = origins[robot][X_INDEX][letter]
						pass
					pass

					if origins[robot][Y_INDEX]:
						if number in origins[robot][Y_INDEX].keys():
							local_vars['ORIGY'] = origins[robot][Y_INDEX][number]
						pass
					pass
				pass
			pass
			
			line_index             =  0
			current_section_index  = -1
			link_lines             = []
			tcp_lines              = []
			is_reading_coordinates = False
			while line_index < len(in_lines):
				line = in_lines[line_index]

				#
				# Lettura Coordinate
				# ================================================================================================
				if is_reading_coordinates:
					if in_str(line, MARK_SECTION_END):
						is_reading_coordinates = False
						tcp_lines = [line]
					else:
						#
						# Ricerca Z (per maschere)
						# ================================================================================================
						search = line.find('Z')
						if search >= 0:
							Z_coord = str_get_number_or_nothing(line[search+1:])
							if Z_coord not in program_Zs:
								program_Zs.append(Z_coord)
							pass
						pass

						#
						# Operazioni maschere
						# ================================================================================================
						if local_vars['MASCHERA_TYPE'] != MASCHERA_NOMASCHERA:
							if local_vars['MASCHERA_DEPTH'] == MASCHERA_15MM:
								#
								# Sostituzione Z-5 per maschere numeri 15mm
								# ================================================================================================
								sub_z = ''
								if local_vars['MASCHERA_TYPE'] == MASCHERA_BASE:
									sub_z = config['maschera_15mm_base_sostituzione_z-5']
								else:
									sub_z = config['maschera_15mm_numeri_sostituzione_z-5']
								pass

								if sub_z and (sub_z != '-5'):
									line = line.replace('Z-5', 'Z' + sub_z)
								pass
							pass

							# Sosituzioni Z25 e F2000
							line = line.replace('Z25.000', 'Z40F15000').replace('F2000','F3500')
						pass

						#
						# Rimozione Nxx a inizio riga
						# ================================================================================================
						if line[0] == 'N':
							removee = 'N'
							removee += str_get_number_or_nothing(line[1:])
							line = line.replace(removee, '').strip()
						pass
						
						#
						# Ottimizzazione link
						# ================================================================================================
						if config['ottimizza_link']:
							if 'FINE LINK' in line:
								test_line = nc_sections[current_section_index][NCSEC_COORDINATES].pop()
								while 'INIZIO LINK' not in test_line:
									link_lines = [test_line] + link_lines
									if 'Z' in test_line:
										nc_sections[current_section_index][NCSEC_COORDINATES].extend(link_lines)
										link_lines = []

										warning_text = ui_warn(warning_text, 'Variazione Z durante un link, ottimizzazione saltata')
										break
									pass
									test_line  = nc_sections[current_section_index][NCSEC_COORDINATES].pop()
								pass

								if len(link_lines) > 0:
									nc_sections[current_section_index][NCSEC_COORDINATES].append(test_line)
									nc_sections[current_section_index][NCSEC_COORDINATES].append(link_lines[-1])
									link_lines = []
								pass
							pass
						pass

						#
						# G00, G01 -> G0, G1
						# ================================================================================================
						if config['sostituisci_g00_g01']:
							line = line.replace('G00', 'G0')
							line = line.replace('G01', 'G1')
						pass

						#
						# Spaziatura coordinate
						# ================================================================================================
						if config['numero_spazi_tra_coordinate'] > 0:
							n_spaces = config['numero_spazi_tra_coordinate']

							indices = []
							was_numeric = False
							for i in range(len(line)):
								if line[i].isnumeric() or line[i] == '.':
									was_numeric = True
								elif line[i].isalpha():
									if was_numeric:
										indices = [i] + indices
									pass
									was_numeric = False
								pass
							pass

							for i in indices:
								line = str_insert(line, ' '*n_spaces, i)
							pass
						pass

						#
						# Numerazione riga
						# ================================================================================================
						if config['righe_numerate']:
							line_number_str = 'N' + str(line_number)
							if config['numerazione_righe_sulla_destra']:
								padding = config['distanza_numeri_righe'] - len(line_number_str) - len(line)
								if padding < 0:
									padding = 5
								pass
								line += ' '*padding + line_number_str
							else:
								padding = config['distanza_numeri_righe']- len(line_number_str)
								if padding <= 0:
									padding = 2
								pass
								line = line_number_str + padding * ' ' + line
							pass
							line_number += 1
						pass


						#
						# Aggiunta riga al set di coordinate
						# ================================================================================================
						nc_sections[current_section_index][NCSEC_COORDINATES].append(line)
					pass
				else:
					tcp_lines.append(line)

					if in_str(line, MARK_SECTION_START):
						is_l385 = False
						for tcp_line in tcp_lines:
							if "L385" in tcp_line:
								is_l385 = True
								break
							pass
						pass

						if not is_l385:
							nc_sections[current_section_index][NCSEC_COORDINATES].extend(tcp_lines)
						pass
						tcp_lines = []
						is_reading_coordinates = True
					pass
				pass

				#
				# Lettura Fresa/Disco
				#         se la riga contiene la descrizione di un utensile, comincia una nuova sezione
				# ================================================================================================
				search_index  = line.find(SEARCH_FRESA)
				utensile_type = 'F'
				if search_index == -1:
					search_index = line.find(SEARCH_DISCO)
					utensile_type = 'D'
				pass
				if search_index >= 0:
					# Nuova sezione
					nc_sections.append([None] * NCSEC_TOTAL)
					current_section_index += 1
					nc_sections[current_section_index][NCSEC_COORDINATES] = []

					nc_sections[current_section_index][NCSEC_UTENSILE] = (utensile_type + 
																		  str_get_number_ignore_any_before(line[search_index:]).\
																		  rstrip('0').rstrip('.'))
				pass

				#
				# Lettura L385
				# ================================================================================================
				search_index = line.find(SEARCH_L385)
				if search_index >= 0:
					nc_sections[current_section_index][NCSEC_LUNGHEZZA] = \
						str_get_number_ignore_any_before(line[search_index + len(SEARCH_L385):]).rstrip('0').rstrip('.')
				pass

				#
				# Lettura L386
				# ================================================================================================
				search_index = line.find(SEARCH_L386)
				if search_index >= 0:
					nc_sections[current_section_index][NCSEC_MOTORE] = \
						str_get_number_ignore_any_before(line[search_index + len(SEARCH_L386):])
				pass
				
				line_index += 1
			pass
		pass

		if (local_vars['MASCHERA_TYPE'] != MASCHERA_NOMASCHERA):
			expected_Zs = ['100.000', '25.000', '10.000', '-5.000']
			for zz in expected_Zs:
				if zz in program_Zs:
					program_Zs.remove(zz)
				else:
					warning_text = ui_warn(warning_text, 'Z' + zz + ' assente')
				pass
			pass

			if len(program_Zs) > 0:
				for z in program_Zs:
					if not z:
						z = '0'
					pass
					warning_text = ui_warn(warning_text, 'Z' + z)
				pass
			pass

			if len(nc_sections) > 1:
				warning_text = ui_warn(warning_text, '{} utensili'.format(len(nc_sections)))
			pass
		pass

		with open('out/' + filename, 'w') as fout:

			fout_content = ''
			utensili_utilizzati = [None, None, None]
			repeating_vars = dict()                      # {'file.template' : n_of_repeats_left}

			for section in nc_sections:
				#
				# Parsing prima coordinata
				# ================================================================================================
				local_vars['PRIMAX'] = str_get_coordinate('X', section[NCSEC_COORDINATES][0])
				local_vars['PRIMAY'] = str_get_coordinate('Y', section[NCSEC_COORDINATES][0])
				local_vars['PRIMAZ'] = str_get_coordinate('Z', section[NCSEC_COORDINATES][0])
				local_vars['PRIMAA'] = str_get_coordinate('A', section[NCSEC_COORDINATES][0])
				local_vars['PRIMAB'] = str_get_coordinate('B', section[NCSEC_COORDINATES][0])
				local_vars['PRIMAC'] = str_get_coordinate('C', section[NCSEC_COORDINATES][0])
				if not local_vars['PRIMAX']:
					local_vars['PRIMAX'] = 'INESISTENTE'
				if not local_vars['PRIMAY']:
					local_vars['PRIMAY'] = 'INESISTENTE'
				if not local_vars['PRIMAZ']:
					local_vars['PRIMAZ'] = 'INESISTENTE'
				if not local_vars['PRIMAA']:
					local_vars['PRIMAA'] = 'INESISTENTE'
				if not local_vars['PRIMAB']:
					local_vars['PRIMAB'] = 'INESISTENTE'
				if not local_vars['PRIMAC']:
					local_vars['PRIMAC'] = 'INESISTENTE'

				#
				# Compilazione informazioni sezione
				# ================================================================================================
				local_vars['LUNGHEZZAUTENSILE'] = section[NCSEC_LUNGHEZZA]
				local_vars['NUMEROMOTORE']      = section[NCSEC_MOTORE]
				local_vars['UTENSILE']          = section[NCSEC_UTENSILE]

				coordinates_start = 1
				if config['mantieni_prima_coordinata']:
					coordinates_start = None
				pass

				local_vars['COORDINATE']        = '\n'.join(section[NCSEC_COORDINATES][coordinates_start:])


				#
				# Raccolta informazioni utensili (usati dopo, per header)
				# ================================================================================================
				n_motore = int(section[NCSEC_MOTORE]) - 2
				if (n_motore < 0) or (n_motore > 2):                                   # @todo: make configurable
					report_error_and_exit(ui_text, "Numero motore invalido ({})".format(n_motore + 2))
				elif ( (utensili_utilizzati[n_motore] != None) and \
					   ( (utensili_utilizzati[n_motore][MOTORE_UTENSILE] != section[NCSEC_UTENSILE]) or \
					     (utensili_utilizzati[n_motore][MOTORE_LUNGHEZZA] != section[NCSEC_LUNGHEZZA]))):
					report_error_and_exit(ui_text, "Il motore {} è usato più volte con utensili differenti".format(n_motore + 2))
				pass
				utensili_utilizzati[n_motore] = [None, None]
				utensili_utilizzati[n_motore][MOTORE_UTENSILE]  = section[NCSEC_UTENSILE]
				utensili_utilizzati[n_motore][MOTORE_LUNGHEZZA] = section[NCSEC_LUNGHEZZA]

				#
				# Parte programma per utensile
				# ================================================================================================
				template = read_and_process_template('utensile.template', local_vars, repeating_vars)


				local_vars['LUNGHEZZAUTENSILE'] = '__ERRORE'
				local_vars['NUMEROMOTORE']      = '__ERRORE'
				local_vars['UTENSILE']          = '__ERRORE'
				local_vars['COORDINATE']        = '__ERRORE'
				local_vars['PRIMAX'] = '__ERRORE'
				local_vars['PRIMAY'] = '__ERRORE'
				local_vars['PRIMAZ'] = '__ERRORE'
				local_vars['PRIMAA'] = '__ERRORE'
				local_vars['PRIMAB'] = '__ERRORE'
				local_vars['PRIMAC'] = '__ERRORE'
				fout_content += template
			pass
			
			if local_vars.get('MASCHERA_TYPE', MASCHERA_NOMASCHERA) == MASCHERA_NOMASCHERA:
				#
				# Preparazione testo utensili
				# ================================================================================================
				ut_text = ''
				for n_mot in range(3):
					if utensili_utilizzati[n_mot] != None:
						ut_text += 'M{} {} L{} - '.format(n_mot+2, utensili_utilizzati[n_mot][0], utensili_utilizzati[n_mot][1])
					pass
				pass
				if ut_text:
					ut_text = ut_text[:-3]
					local_vars['UTENSILI'] = ut_text
				pass

				ui_text += '(' + ut_text + ')'


				#
				# Righe codici
				# ================================================================================================
				local_vars['RIGHECODICI'] = ''
				if len(local_vars['all_CODICI']) == 0:
					local_vars['all_CODICI'].append((local_vars['CODICE'], local_vars['CODICELAPI'], ''))
				pass

				for code in local_vars['all_CODICI']:
					local_vars['CODICE']     = code[CODE_CODICE]
					local_vars['CODICELAPI'] = code[CODE_LAPI]
					if code[CODE_REV]:
						local_vars['REV'] = 'Rev.' + code[CODE_REV]
					else:
						local_vars['REV'] = ''
					pass

					local_vars['RIGHECODICI'] += read_and_process_template('riga_codice.template', local_vars, repeating_vars)
				pass
				local_vars['RIGHECODICI'] = local_vars['RIGHECODICI'].rstrip('\n')
			pass

			#
			# Intestazione
			# ================================================================================================
			header = read_and_process_template('intestazione.template', local_vars, repeating_vars)
			fout_content = header + fout_content

			#
			# Chiusura
			# ================================================================================================
			footer = read_and_process_template('chiusura.template', local_vars, repeating_vars)
			fout_content += footer

			fout.write(fout_content)
		pass
	pass
	if ui_text:
		if warning_text:
			warning_text = warning_text[:-2] + ']'

			if (term_size != None):
				max_len = term_size.columns - len(ui_text) - len(WARNING_INTRODUCTION)

				if max_len >= 10:   # @note: if we have less than 10 columns to work with, it's better to let it wrap with the default behavior
					colon_index   = len(WARNING_INTRODUCTION)
					processed_len = colon_index

					# @note: colon_index, in theory, should never be == -1
					while (len(warning_text) - processed_len) > max_len:
						last_colon_index = warning_text.find('; ') + 1

						last_space_index = warning_text.rfind(' ', processed_len, processed_len + max_len)
						if last_space_index < 0:
							last_space_index = warning_text.find(' ', processed_len + max_len)
						pass

						last_index = last_space_index
						if (last_colon_index > 0) and (last_colon_index < last_index):
							last_index = last_colon_index
						pass

						if last_index > 0:
							warning_text = str_replace_at_index(warning_text, last_index, '\n')
							processed_len = last_index + 1
						else:
							break
						pass
					pass

					warning_text = warning_text.replace('\n', '\n' + ' '*(len(ui_text) + colon_index))
				pass
			pass
			ui_text += warning_text
		pass

		print(ui_text)
	pass
pass

if __name__ == '__main__':
	print("TEXporter v{}\n".format(_VERSION))

	paths            = glob.glob('in/*')
	config_taglio    = load_config(False)
	config_maschera  = load_config(True)
	origins          = load_origins()
	if not os.path.exists('out'):
	    os.makedirs('out')

	all_vars = load_all_vars(config_taglio)

	max_filename_len = 0
	for path in paths:
		if not os.path.isdir(path):
			this_len = len(os.path.basename(path))
			if this_len > MAX_UI_FILENAME_LEN:
				this_len = MAX_UI_FILENAME_LEN
			pass

			if this_len > max_filename_len:
				max_filename_len = this_len
			pass
		pass
	pass

	for path in paths:
		if not os.path.isdir(path):
			filename = os.path.basename(path)
			if not ('maschera' in filename.lower()):
				process(filename, config_taglio, all_vars, origins,   max_filename_len, False)
			else:
				process(filename, config_maschera, all_vars, origins, max_filename_len, True)
			pass
		pass
	pass

	print("\n\nPremere invio per chiudere...", end='')
	while True:
		event = keyboard.read_event()
		if (event.name == 'enter') and (event.event_type == 'up'):
			break
		pass
	pass
pass
