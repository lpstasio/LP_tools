# TEXporter
_VERSION = 0

# CHANGELOG
#   v0: Riconosce le diverse sezioni di cui è composto il programma.
#        Per 'sezione' si intende una parte di programma che va da un'attivazione del tcp alla successiva disattivazione;
#        ogni sezione è caratterizzata da un motore, un utensile e una lunghezza utensile
# PLANNED
#   config: robots
#           L385/L386 substitutes?

import os, glob

NCSEC_MOTORE      = 0
NCSEC_UTENSILE    = 1
NCSEC_LUNGHEZZA   = 2
NCSEC_COORDINATES = 3
NCSEC_TOTAL       = 4

SEARCH_L385  = 'L385'
SEARCH_L386  = 'L386'
SEARCH_FRESA = 'FRESA CILINDRICA'
SEARCH_DISCO = 'FRESA SFERICA'
MARK_SECTION_START = '(TCP,'
MARK_SECTION_END   = ['(TCP)', 'FINE PROGRAMMA']

def str_get_number_ignore_any_before(s):
	result = ''
	for c in s:
		if (c.isdecimal()) or (c == '.') or (c == '-'):
			result += c
		elif result:
			break
		pass
	pass
	return result
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
			
			line_index             = 0
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
					nc_sections[current_section_index][NCSEC_LUNGHEZZA] = str_get_number_ignore_any_before(line[search_index + len(SEARCH_L385):]).rstrip('.0')
				pass

				#
				# Lettura L386
				# ================================================================================================
				search_index = line.find(SEARCH_L386)
				if search_index >= 0:
					nc_sections[current_section_index][NCSEC_MOTORE] = str_get_number_ignore_any_before(line[search_index + len(SEARCH_L386):])
				pass
				
				#section[NCSEC_COORDINATES] = pass
				line_index += 1
			pass
		pass

		with open('out/' + filename, 'w') as fout:
			for section in nc_sections:
				fout.write('L385 = ' + section[NCSEC_LUNGHEZZA] + '\n')
				fout.write('L386 = ' + section[NCSEC_MOTORE] + '\n')
				fout.write(section[NCSEC_UTENSILE] + '\n')
				for line in section[NCSEC_COORDINATES]:
					fout.write(line + '\n')
				pass
			pass
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
