# TEXporter
_VERSION = 0

# CHANGELOG
#   v0: Riconosce le diverse sezioni di cui è composto il programma.
#        Per 'sezione' si intende una parte di programma che va da un'attivazione del tcp alla successiva disattivazione;
#        ogni sezione è caratterizzata da un motore, un utensile e una lunghezza utensile
# PLANNED
#   config: robots
#           L385/L386 substitutes?
#           config compiler
#           custom variables
#           IMPORTANT: when compiling config, if no 'PRIMAX/Y/Z/A/B' is used, warn and keep first coordinate
#           add C axis support
#           revision alpha/numeric mix
#           robot directive ('r2') preferred position (on the right or on the left)
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
#            "desc_max_lunghezza_prima_riga" : "34",
#            "desc_max_lunghezza"            : "45",
#            "formato_data"                  : "g.m.aaaa",

import os, glob
from datetime import datetime

NCSEC_MOTORE      = 0
NCSEC_UTENSILE    = 1
NCSEC_LUNGHEZZA   = 2
NCSEC_COORDINATES = 3
NCSEC_TOTAL       = 4
MOTORE_UTENSILE   = 0
MOTORE_LUNGHEZZA  = 1


# @todo: move into config
SEARCH_L385  = 'L385'
SEARCH_L386  = 'L386'
SEARCH_FRESA = 'FRESA CILINDRICA'
SEARCH_DISCO = 'FRESA SFERICA'
MARK_SECTION_START = '(TCP,'
MARK_SECTION_END   = ['(TCP)', 'FINE PROGRAMMA']

default_vars = {
	'POSIZIONEDIMA'                  : 'XX',
	'ORIGX'                          : '',
	'ORIGY'                          : '',
	'ORIGZ'                          : ''
}
default_config = {
	"stringa_cliente"                      : "CLIENTE",
	"stringa_descrizione_pezzo"            : "DESCRIZIONE PEZZO",
	"stringa_codice"                       : "CODICE PEZZO",
	"stringa_revisione"                    : "REV",
	"stringa_nome_programma"               : "NOTE",
	"descrizione_max_lunghezza_prima_riga" : "34",
	"descrizione_max_lunghezza"            : "45",
	"formato_data"                         : "g.m.aaaa"
}


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
	return _str_get_number(s, True)
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


def read_template_raw(filename):
	template  = ''
	variables = []
	if os.path.exists('config/' + filename):
		with open('config/' + filename, 'r') as file:
			template = file.read()
		pass

		if template:
			mark_count = template.count('$')
			if (mark_count % 2):
				print("Errore: nel template '" + filename + "' sono presenti un numero dispari di '$'")
				__ERROR_UNMATCHED_DOLLAR
			pass

			mark_start = template.find('$')
			while mark_start >= 0:
				mark_end = template.find('$', mark_start+1)
				var_name = template[mark_start+1 : mark_end]
				if not var_name:
					print("Errore: due '$' non racchiudono il nome di una variabile nel template '" + filename + "'")
					__ERROR_NULL_VARIABLE_NAME
				pass

				if not (var_name in variables):
					variables.append(var_name)
				pass
				mark_start = template.find('$', mark_end+1)
			pass
		pass
	else:
		# @todo: report error
		print("DEBUG: template '{}' non trovato".format(filename))
	pass
	return template, variables
pass


def read_and_process_template(filename, variable_database, repeating_vars):
	template, pending_vars = read_template_raw(filename)
	for var in pending_vars:
		if ':' in var:                                      # file references
			var_segments = var.split(':')
			if len(var_segments) > 2:
				print("Errore: il riferimento a file '{}' nel template '{}' contiene due o più ':'".format(var, filename))
				__SYNTAX_ERROR_FILE_REFERENCE
			pass

			repeat_count    = var_segments[0]
			referenced_file = var_segments[1]
			if referenced_file == filename:
				print("ERRORE: il template '{}' contiene un riferimento a se stesso")
				__ERROR_RECURSIVE_TEMPLATE
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


def parse_tex(filename):
	vars = dict()

	if os.path.exists('config/' + filename):
		with open('config/' + filename, 'r') as tfile:
			line_number = 0
			for org_line in tfile.read().splitlines():
				line_number += 1

				line = org_line
				comment_start = line.find(';')
				if comment_start >= 0:
					line = line[:comment_start].strip()
				pass

				if line:
					separator_index = line.find(':')
					if separator_index < 0:
						print("ERRORE: nessun ':' trovato;\n  config/{}""[{}]: '{}'\n".\
							  format(filename, line_number, org_line))
						__ERROR_VARIABLE_DEFINITION_SYNTAX_ERROR
					pass

					var_name  = line[:separator_index].replace(' ', '')
					var_value = line[separator_index + 1:].lstrip()
					
					if not var_name:
						print("ERRORE: definizione variabile senza nome;\n  config/{}[{}]: '{}'\n".\
							  format(filename, line_number, org_line))
						__ERROR_VARIABLE_DEFINITION_EMPTY_NAME
					pass
					
					if var_name in vars.keys():
						print("Attenzione: variabile precedentemente definita, il nuovo valore sarà ignorato;\n  config/{}[{}]: '{}'\n".\
							  format(filename, line_number, org_line))
					else:
						vars[var_name] = var_value
					pass
				pass
			pass
		pass
	pass
	return vars
pass


def load_config():
	#
	# Lettura configurazione
	# ================================================================================================
	config = parse_tex('configurazione.tex')

	#
	# Inserimento valori default per variabili non specificate
	# ================================================================================================
	forced_config = default_config.copy()
	forced_config.update(config)
	config = forced_config

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

	return config
pass


# @todo: robot specific variable override
def load_vars(config, robot = 0):
	#
	# Lettura variabili
	# ================================================================================================
	vars = parse_tex('variabili.tex')
	vars['DATA'] = datetime.now().strftime(config['formato_data'])

	#
	# Inserimento valori default per variabili non specificate
	# ================================================================================================
	forced_vars = default_vars.copy()
	forced_vars.update(vars)
	vars = forced_vars

	if robot > 0:
		vars.update(parse_tex('r{}/variabili.tex'.format(robot)))
	pass

	return vars
pass


def load_program_info(filename, content, config):
	result = {
		'PROGRAMMA'               : 'PRG0123',
		'CLIENTE'                 : 'cliente',
		'DESCRIZIONE_PRIMA_RIGA'  : 'Descrizione',
		'DESCRIZIONE_ALTRE_RIGHE' : '',
		'CODICE'			      : '00.00.00.00',
		'UTENSILI'                : 'UTENSILI',
		'ROBOT'                   : '',
		'REV'                     : ''
	}

	#
	# Robot
	# ================================================================================================
	robot_id = ''
	search_end_index = None
	while not robot_id:
		search = filename[:search_end_index].lower().rfind('r')                    # @todo: make configurable
		if search >= 0:
			robot_id = str_get_number_or_nothing(filename[search+1:])
			search_end_index = search
		else:
			break
		pass

		if robot_id:
			robot_id = robot_id.rstrip('.')
			as_number = int(robot_id)
			if ('.' in robot_id) or (as_number < 0) or (as_number > 100):
				robot_id = ''
			pass
		pass
	if robot_id:
		result['ROBOT'] = robot_id

	#
	# Cliente
	# ================================================================================================
	search = str_get_value(content, config['stringa_cliente'])
	if search:
		result['CLIENTE'] = search.lower()

	#
	# Descrizione
	# ================================================================================================
	descrizione = result['DESCRIZIONE_PRIMA_RIGA']
	search = str_get_value(content, config['stringa_descrizione_pezzo'])
	if search:
		descrizione = search.capitalize()

	#
	# Formattazione descrizione
	# ================================================================================================
	desc_first_line_max_length = int(config.get('_desc_max_lunghezza_prima_riga', '34'))
	desc_other_line_max_length = int(config.get('_desc_max_lunghezza', '45'))

	if len(descrizione) <= desc_first_line_max_length:
		descrizione = [descrizione]
	else: # len_desc > desc_first_line_max_length
		max_len = desc_first_line_max_length
		processed_len = 0
		while (len(descrizione_pezzo) - processed_len) > max_len:
			last_space_index = descrizione_pezzo.rfind(' ', processed_len, processed_len + max_len)
			if last_space_index < 0:
				last_space_index = descrizione_pezzo.find(' ', processed_len + max_len)
			pass

			if last_space_index > 0:
				descrizione_pezzo = str_replace_at_index(descrizione_pezzo, last_space_index, '\n; ')
				processed_len = last_space_index + 3
			else:
				break
			pass
			max_len = desc_other_line_max_length
		pass
		descrizione = descrizione.split('\n')
	pass

	result['DESCRIZIONE_PRIMA_RIGA']  = descrizione[0].ljust(desc_first_line_max_length, ' ')
	if len(descrizione) > 1:  # descrizione ha più di una riga
		descrizione[1] = '\n' + descrizione[1]
		result['DESCRIZIONE_ALTRE_RIGHE'] = '\n'.join(descrizione[1:])
	pass

	#
	# Codice
	# ================================================================================================
	search = str_get_value(content, config['stringa_codice'])
	if search:
		result['CODICE'] = search.upper()

	#
	# Revisione
	# ================================================================================================
	rev_search = content.find(config['stringa_revisione'])
	rev_value = ''
	if rev_search >= 0:
		rev_search += len(config['stringa_revisione'])

		# getting next alphanumeric
		is_numeric = False
		is_started = False
		for c in content[rev_search:]:
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
		result['REV'] = 'Rev.' + rev_value

	#
	# Nome programma
	# ================================================================================================
	search = str_get_value(content, config['stringa_nome_programma'], ' ', '\n')
	if search:
		result['PROGRAMMA'] = search.upper()
		if len(result['PROGRAMMA']) != 7:
			print("ATTENZIONE: nome '" + result['PROGRAMMA'] + "' è composto da", len(result['PROGRAMMA']), "caratteri")
		pass
	pass
	return result
pass

def process(filename):
	should_overwrite = True
	if os.path.exists('out/' + filename):
		pass # @todo: prompt overwrite
	pass

	nc_sections = []
	in_content = None
	in_lines   = None
	if should_overwrite:
		with open('in/' + filename,'r') as fin:
			in_content = fin.read()
			in_lines = in_content.splitlines()

			config = load_config()
			vars   = load_program_info(filename, in_content, config)

			robot  = vars['ROBOT']
			if not robot:
				robot = '0'
			robot = int(robot)

			vars.update(load_vars(config, robot))
			
			line_index             =  0
			current_section_index  = -1
			is_reading_coordinates = False
			while line_index < len(in_lines):
				line = in_lines[line_index]

				#
				# Lettura Coordinate
				# ================================================================================================
				if is_reading_coordinates:
					if in_str(line, MARK_SECTION_END):
						is_reading_coordinates = False
					else:
						nc_sections[current_section_index][NCSEC_COORDINATES].append(line)
					pass
				elif in_str(line, MARK_SECTION_START):
					is_reading_coordinates = True
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

					nc_sections[current_section_index][NCSEC_UTENSILE] = utensile_type + str_get_number_ignore_any_before(line[search_index:]).rstrip('.0')
				pass

				#
				# Lettura L385
				# ================================================================================================
				search_index = line.find(SEARCH_L385)
				if search_index >= 0:
					nc_sections[current_section_index][NCSEC_LUNGHEZZA] = str_get_number_ignore_any_before(line[search_index + len(SEARCH_L385):]).rstrip('0').rstrip('.')
				pass

				#
				# Lettura L386
				# ================================================================================================
				search_index = line.find(SEARCH_L386)
				if search_index >= 0:
					nc_sections[current_section_index][NCSEC_MOTORE] = str_get_number_ignore_any_before(line[search_index + len(SEARCH_L386):])
				pass
				
				line_index += 1
			pass
		pass

		with open('out/' + filename, 'w') as fout:

			fout_content = ''
			utensili_utilizzati = [None, None, None]
			repeating_vars = dict()                      # 'file.template' : n_of_repeats_left


			for section in nc_sections:
				#
				# Parsing prima coordinata
				# ================================================================================================
				vars['PRIMAX'] = str_get_coordinate('X', section[NCSEC_COORDINATES][0])
				vars['PRIMAY'] = str_get_coordinate('Y', section[NCSEC_COORDINATES][0])
				vars['PRIMAZ'] = str_get_coordinate('Z', section[NCSEC_COORDINATES][0])
				vars['PRIMAA'] = str_get_coordinate('A', section[NCSEC_COORDINATES][0])
				vars['PRIMAB'] = str_get_coordinate('B', section[NCSEC_COORDINATES][0])
				vars['PRIMAC'] = str_get_coordinate('C', section[NCSEC_COORDINATES][0])
				if not vars['PRIMAX']:
					vars['PRIMAX'] = 'INESISTENTE'
				if not vars['PRIMAY']:
					vars['PRIMAY'] = 'INESISTENTE'
				if not vars['PRIMAZ']:
					vars['PRIMAZ'] = 'INESISTENTE'
				if not vars['PRIMAA']:
					vars['PRIMAA'] = 'INESISTENTE'
				if not vars['PRIMAB']:
					vars['PRIMAB'] = 'INESISTENTE'
				if not vars['PRIMAC']:
					vars['PRIMAC'] = 'INESISTENTE'

				#
				# Compilazione informazioni sezione
				# ================================================================================================
				vars['LUNGHEZZAUTENSILE'] = section[NCSEC_LUNGHEZZA]
				vars['NUMEROMOTORE']      = section[NCSEC_MOTORE]
				vars['UTENSILE']          = section[NCSEC_UTENSILE]
				vars['COORDINATE']        = '\n'.join(section[NCSEC_COORDINATES][1:])

				#
				# Raccolta informazioni utensili
				# ================================================================================================
				n_motore = int(section[NCSEC_MOTORE]) - 2
				if (n_motore < 0) or (n_motore > 2):         # @todo: make configurable
					___ERRORE_N_MOTORE_NON_VALIDO
				elif ( (utensili_utilizzati[n_motore] != None) and \
					   ( (utensili_utilizzati[n_motore][MOTORE_UTENSILE] != section[NCSEC_UTENSILE]) or \
					     (utensili_utilizzati[n_motore][MOTORE_LUNGHEZZA] != section[NCSEC_LUNGHEZZA]))):
					___ERRORE_N_MOTORE_DUPLICATO
				pass
				utensili_utilizzati[n_motore] = [None, None]
				utensili_utilizzati[n_motore][MOTORE_UTENSILE]  = section[NCSEC_UTENSILE]
				utensili_utilizzati[n_motore][MOTORE_LUNGHEZZA] = section[NCSEC_LUNGHEZZA]

				#
				# Parte programma per utensile
				# ================================================================================================
				template = read_and_process_template('utensile.template', vars, repeating_vars)


				vars['LUNGHEZZAUTENSILE'] = '__ERRORE'
				vars['NUMEROMOTORE']      = '__ERRORE'
				vars['UTENSILE']          = '__ERRORE'
				vars['COORDINATE']        = '__ERRORE'
				vars['PRIMAX'] = '__ERRORE'
				vars['PRIMAY'] = '__ERRORE'
				vars['PRIMAZ'] = '__ERRORE'
				vars['PRIMAA'] = '__ERRORE'
				vars['PRIMAB'] = '__ERRORE'
				vars['PRIMAC'] = '__ERRORE'
				fout_content += template
			pass
			
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
				vars['UTENSILI'] = ut_text
			pass

			#
			# Intestazione
			# ================================================================================================
			header = read_and_process_template('intestazione.template', vars, repeating_vars)
			fout_content = header + fout_content

			#
			# Chiusura
			# ================================================================================================
			footer = read_and_process_template('chiusura.template', vars, repeating_vars)
			fout_content += footer

			fout.write(fout_content)
		pass
	pass
pass

if __name__ == '__main__':
	print("TEXporter v{}".format(_VERSION))

	paths = glob.glob('in/*')
	if not os.path.exists('out'):
	    os.makedirs('out')
	for path in paths:
		if not os.path.isdir(path):
			filename = os.path.basename(path)
			if not ('maschera' in filename.lower()):
				process(filename)
			pass
		pass
	pass
pass
