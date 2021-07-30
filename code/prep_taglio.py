import re
import glob
import os

VERSION_NUMBER = 5

# CHANGELOG
#   v2: '(UIO,X,Y,Z)' era precedente inserito ad ogni cambio di utensile, invece che solo in quello iniziale
#       Aggiunto supporto per '(TCP)' e '(TCP,1)' senza cambio utensile
#   v4: Riconosce 'R2'/'r2' e 'R9'/'r9' nel nome del file ed esporta le modifiche necessarie
#       Riconosce qualsiasi estensione, non solo .nc
#       Cambiato l'header
#   v5: Riconosce 'INIZIO LINK' e 'FINE LINK' e lascia solo una riga tra i due; (se una Z viene trovata dopo un 'INIZIO LINK' e prima di un 'FINE LINK', esporta tutte le righe senza modifiche)
#
#
# PLANNED:
#   Data nell'header
#   R3, R4, R5, R6
#   Posizioni dime
#   Input nome?
#   Centratura utensili in header
#   Numerazione righe

nome_programma     = 'NOME_PROGRAMMA'
nome_programmatore = ''
dima               = 'XX'
n_robot            = 'X'

MOTORE_UTENSILE  = 0
MOTORE_LUNGHEZZA = 1

info_text_blank = '''
;
;
;
;
'''[1:]

info_text = '''
;                        __NOMEPR__
;  <R__NROBOT__>  __DIMA__                   __PROGRAMMATORE__
;                     __UTENSILI__
;
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
__ORIGIN__G90 G0 __X__ __Y__ __B__ __A__
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

def process(name):
	robot_number = 0

	info_inserted    = False
	is_writing       = True
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

	if ('r2' in name.lower()):
		robot_number = 2
	elif ('r9' in name.lower()):
		robot_number = 9

	with open('in/' + name,'r') as fin:
		should_overwrite = True
		if os.path.exists('out/' + name):
			choice = input("\nIl file '" + name + "' esiste nella cartella 'out', sovrascrivere? [Sn] ")
			should_overwrite = choice[0].lower() == 's'
		if should_overwrite:
			with open('out/' + name, 'w') as fout:
				# ricerca utensili
				fin_content = fin.read()
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

				# Preparazione info
				utensili_text = ''
				for i in range(3):
					if motori[i] != None:
						utensili_text += 'M{} {} L{} - '.format(i+2, motori[i][0], motori[i][1])
				utensili_text = utensili_text[:-3]

				robot_text = ''
				if (robot_number > 0):
					robot_text = ' [R' + str(robot_number) + ']'
				print(name, robot_text + ' (' + utensili_text + ')')


				for line in fin_content.split('\n'):
					line += '\n'
					if not info_inserted:
						if '(TCP)' in line:
							is_writing = False
						if 'DIS' in line:       # Info iniziale
							fout.write(info_text.\
									   replace('__NOMEPR__', nome_programma).\
									   replace('__UTENSILI__', utensili_text).\
									   replace('__DIMA__', dima).\
									   replace('__NROBOT__', n_robot).\
									   replace('__PROGRAMMATORE__', nome_programmatore))
							info_inserted = True
							is_writing = True
							tcp0_found = True
					else:  # info_inserted == True
						if tcp0_found and (not tcp1_found):
							if 'DIS' in line:
								is_writing = True
							else:
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

									fout.write(start_text.\
												replace('__ORIGIN__',    origin).\
												replace('__NMOTORE__',   current_mot).\
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
				elif robot_number == 9:
					process_r2_r9(name, True)
				os.remove('out/temp')

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

if __name__ == '__main__':
	paths = glob.glob('in/*')
	if not os.path.exists('out'):
	    os.makedirs('out')

	print("PREPARAZIONE TAGLIO (v{})\n\n".format(VERSION_NUMBER))
	for path in paths:
		if not os.path.isdir(path):
			filename = os.path.basename(path)
			if not ('maschera' in filename.lower()):
				process(filename)
	
	input("\n\nPremere invio per chiudere...")

